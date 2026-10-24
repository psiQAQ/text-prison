/** Explicit experiment-only tools. No shell or arbitrary executable access. */
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {Type} from '@earendil-works/pi-ai';
import {makeBoundary} from './tool_boundary.mjs';

export default function(pi) {
  const config = JSON.parse(fs.readFileSync(process.env.TEXTPRISON_TOOL_CONFIG, 'utf8'));
  const boundary = makeBoundary(config);
  const result = (text) => ({content: [{type: 'text', text}], details: undefined});
  // Pi's native skill catalog is exposed only when a tool named read or bash exists.
  // This explicit replacement retains read's discovery role while enforcing our file boundary.
  pi.registerTool({name: 'read', label: 'Read permitted file',
    description: 'Read a UTF-8 file within the supplied task workspace or explicitly available skill folder.',
    parameters: Type.Object({path: Type.String()}),
    async execute(_id, args) { return result(boundary.read(args.path)); }});
  pi.registerTool({name: 'write_artifact', label: 'Write task output',
    description: 'Write the full UTF-8 content to an authorized output path. Follow the task revision budget.',
    parameters: Type.Object({path: Type.String(), text: Type.String()}),
    async execute(_id, args) { return result(boundary.write(args.path, args.text)); }});
  if (config.allow_check) pi.registerTool({name: 'check_artifact', label: 'Check task output',
    description: 'Run the fixed artifact checker with the task profile, language, and supplied contract. No commands can be supplied.',
    parameters: Type.Object({path: Type.String(), profile: Type.Optional(Type.String()), language: Type.Optional(Type.String())}),
    async execute(_id, args) {
      const target = boundary.check(args.path);
      if (args.profile && args.profile !== config.profile) throw new Error('Profile differs from frozen task');
      if (args.language && args.language !== config.language) throw new Error('Language differs from frozen task');
      const argv = [config.checker, target, '--profile', config.profile, '--lang', config.language,
        '--format', 'brief', '--report', path.join(config.job_dir, 'mechanical.json')];
      if (config.contract_path) argv.push('--contract', config.contract_path);
      try {
        return result(execFileSync(config.python, argv, {encoding: 'utf8', timeout: 20000, windowsHide: true}));
      } catch (error) {
        if (error.status === 1 && error.stdout) return result(error.stdout);
        throw new Error(`Checker failed: ${String(error.stderr || error.message)}`);
      }
    }});
  let turns = 0;
  pi.on('turn_start', async (_event, ctx) => {
    if (++turns > (config.max_turns ?? 8)) {
      fs.appendFileSync(path.join(config.job_dir, 'tool-audit.jsonl'), JSON.stringify({tool:'turn_budget',allowed:false}) + '\n');
      ctx.abort();
    }
  });
}
