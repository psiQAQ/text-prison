import fs from 'node:fs';
import path from 'node:path';

export function inside(candidate, root) {
  const relative = path.relative(root, candidate);
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}

export function resolveAllowed(name, workspace, roots, mustExist = true) {
  if (typeof name !== 'string' || name.includes('\0')) throw new Error('Invalid path');
  const target = path.resolve(workspace, name);
  let ancestor = target;
  while (!fs.existsSync(ancestor)) {
    const parent = path.dirname(ancestor);
    if (parent === ancestor) throw new Error('No existing path ancestor');
    ancestor = parent;
  }
  const actual = path.resolve(fs.realpathSync(ancestor), path.relative(ancestor, target));
  if (!roots.some(root => inside(actual, fs.realpathSync(root)))) throw new Error('Path is outside permitted roots');
  // Do not allow symlink/junction files within a permitted tree either.
  for (let part = target; part !== path.dirname(part); part = path.dirname(part)) {
    // existsSync follows the target and hides dangling links; lstat inspects the entry itself.
    const entry = fs.lstatSync(part, {throwIfNoEntry: false});
    if (entry?.isSymbolicLink()) throw new Error('Symlink/junction access is not allowed');
    if (roots.some(root => path.resolve(root) === part)) break;
  }
  if (mustExist && !fs.existsSync(actual)) throw new Error('File does not exist');
  return actual;
}

export function makeBoundary(config) {
  const workspace = fs.realpathSync(config.workspace);
  const roots = [workspace, ...(config.skill_path ? [config.skill_path] : [])];
  const writes = new Map();
  let checks = 0;
  const audit = (tool, name, allowed, reason = null) => fs.appendFileSync(path.join(config.job_dir, 'tool-audit.jsonl'),
    JSON.stringify({timestamp: new Date().toISOString(), tool, path: name, allowed, reason}) + '\n', 'utf8');
  function read(name) {
    try {
      const target = resolveAllowed(name, workspace, roots);
      if (inside(target, workspace) && config.readable_paths &&
          !config.readable_paths.some(p => path.resolve(workspace, p) === target)) throw new Error('File is not an authorized input/output');
      if (!fs.statSync(target).isFile() || fs.statSync(target).size > 200000) throw new Error('Expected a text file up to 200 KB');
      const text = fs.readFileSync(target, 'utf8');
      audit('read_file', name, true);
      return text;
    } catch (error) { audit('read_file', name, false, error.message); throw error; }
  }
  function write(name, text) {
    try {
      const target = resolveAllowed(name, workspace, [workspace], false);
      if (!config.writable_paths.some(p => path.resolve(workspace, p) === target)) throw new Error('File is not an authorized output');
      if (typeof text !== 'string' || Buffer.byteLength(text) > 200000) throw new Error('Output exceeds 200 KB');
      const count = writes.get(target) || 0;
      if (count >= (config.max_writes ?? 2)) throw new Error('Output revision limit exhausted');
      fs.mkdirSync(path.dirname(target), {recursive: true});
      fs.writeFileSync(target, text, {encoding: 'utf8', flag: 'w'});
      writes.set(target, count + 1);
      const snapshots = path.join(config.job_dir, 'drafts');
      fs.mkdirSync(snapshots, {recursive: true});
      fs.writeFileSync(path.join(snapshots, `${path.basename(target)}.${count + 1}.txt`), text, 'utf8');
      audit('write_artifact', name, true);
      return `Saved ${path.relative(workspace, target)} (write ${count + 1}).`;
    } catch (error) { audit('write_artifact', name, false, error.message); throw error; }
  }
  function check(name) {
    try {
      if (!config.allow_check || ++checks > 2) throw new Error('Check is unavailable or check budget exhausted');
      const target = resolveAllowed(name, workspace, [workspace]);
      if (!config.writable_paths.some(p => path.resolve(workspace, p) === target)) throw new Error('Not an authorized output');
      audit('check_artifact', name, true);
      return target;
    } catch (error) { audit('check_artifact', name, false, error.message); throw error; }
  }
  return {read, write, check};
}
