"use strict";

const state = {token: "", batchId: "", batch: null, packets: [], packet: null, review: null, stage: "initial", revision: 0, dirty: false, busy: false};
const $ = (id) => document.getElementById(id);
const statusNames = {empty: "未开始", draft: "草稿", submitted: "已提交", frozen: "已冻结", passed: "通过", failed: "有语义错误", uncertain: "存在待定项", not_evaluated: "未完成评价"};
const claimOptions = [["", "请选择"], ["supported", "有来源支持"], ["contradicted", "与来源矛盾"], ["unsupported", "无来源支持"], ["unassessable", "无法判定"]];
const factOptions = [["", "请选择"], ["preserved", "完整保留"], ["missing", "缺失"], ["altered", "含义改变"], ["unassessable", "无法判定"]];
const severityOptions = [["", "无错误 / 未定级"], ["critical", "critical · 关键错误"], ["major", "major · 重大错误"], ["minor", "minor · 局部错误"], ["style_only", "style_only · 仅风格"]];
const errorTypeOptions = [["negation", "否定"], ["modality", "模态 / 必须与建议"], ["condition", "条件"], ["scope", "范围"], ["causality", "因果"], ["actor_object", "主体 / 对象"], ["quantity_unit", "数值 / 单位"], ["time_version", "时间 / 版本"], ["citation", "引用"], ["unsupported_addition", "无来源新增"], ["required_omission", "必需信息遗漏"], ["permission", "权限"], ["execution", "执行要求"], ["other", "其他（请在依据中说明）"]];
const errorStatuses = new Set(["contradicted", "unsupported", "missing", "altered"]);
const aiStatusNames = {completed: "已完成", pending: "待运行", running: "运行中", failed: "运行失败", invalid_review: "评审格式无效", not_run: "未运行", budget_skipped: "预算内未运行"};

function aiOnly() { return state.batch?.review_mode === "ai_only"; }
function aiProgressText(progress) {
  if (!progress.recorded) return "尚无 AI 评审记录";
  const details = Object.entries(progress.statuses).filter(([status]) => status !== "completed").map(([status, count]) => `${aiStatusNames[status] || status} ${count}`);
  return [`已完成 ${progress.completed}/${progress.recorded} 份记录`, ...details].join(" · ");
}

function el(tag, text, cls) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  if (cls) node.className = cls;
  return node;
}
function button(text, handler, cls) {
  const node = el("button", text, cls); node.type = "button"; node.addEventListener("click", handler); return node;
}
function notice(message, error = false) {
  $("notice").textContent = message;
  $("notice").className = message ? `visible${error ? " error" : ""}` : "";
}
function markDirty() {
  state.dirty = true;
  const status = $("save-status"); if (status) status.textContent = "有未保存修改";
}
function field(label, value, onChange, options = {}) {
  const wrapper = el("label", label, "field");
  const input = el(options.options ? "select" : options.line ? "input" : "textarea");
  if (options.options) {
    for (const [key, title] of options.options) { const option = el("option", title); option.value = key; input.append(option); }
  }
  input.value = value ?? "";
  if (options.placeholder) input.placeholder = options.placeholder;
  if (options.rows) input.rows = options.rows;
  input.addEventListener("input", () => { onChange(input.value); markDirty(); });
  wrapper.append(input); return wrapper;
}
async function api(path, body) {
  const options = {cache: "no-store", headers: {}};
  if (body !== undefined) {
    options.method = "POST";
    options.headers = {"Content-Type": "application/json", "X-Review-Token": state.token};
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || `HTTP ${response.status}`);
  return value;
}
function confirmAction(message) {
  $("confirm-message").textContent = message;
  const dialog = $("confirm-dialog");
  const accept = $("confirm-accept"), cancel = $("confirm-cancel");
  // This dialog must remain usable while the surrounding async action is locked.
  accept.disabled = false; cancel.disabled = false;
  return new Promise((resolve) => {
    const finish = (value) => { dialog.close(); accept.removeEventListener("click", yes); cancel.removeEventListener("click", no); dialog.removeEventListener("cancel", escape); resolve(value); };
    const yes = () => finish(true), no = () => finish(false), escape = (event) => { event.preventDefault(); finish(false); };
    accept.addEventListener("click", yes); cancel.addEventListener("click", no); dialog.addEventListener("cancel", escape);
    dialog.showModal(); cancel.focus();
  });
}
async function abandonUnsaved() { return !state.dirty || await confirmAction("当前候选有未保存修改。确定离开？"); }
async function guarded(action) {
  if (state.busy) return;
  state.busy = true;
  document.querySelectorAll("button,input,textarea,select").forEach((node) => { node.dataset.wasDisabled = String(node.disabled); node.disabled = true; });
  try { await action(); } catch (error) { notice(error.message, true); }
  finally {
    state.busy = false;
    document.querySelectorAll("[data-was-disabled]").forEach((node) => { node.disabled = node.dataset.wasDisabled === "true"; delete node.dataset.wasDisabled; });
    if (state.batch) renderSidebar();
  }
}
async function loadBatches(preferred) {
  const data = await api("/api/batches");
  const select = $("batch-select"); select.replaceChildren();
  for (const batch of data.batches) { const option = el("option", `${batch.batch_id} · ${batch.review_mode === "ai_only" ? "AI 评审" : "人工盲评"}`); option.value = batch.batch_id; select.append(option); }
  if (!data.batches.length) { $("workspace").replaceChildren(el("div", "尚未导入评审批次。请等待实验数据准备完成。", "empty")); return; }
  const latestAI = [...data.batches].reverse().find((batch) => batch.review_mode === "ai_only");
  select.value = preferred && data.batches.some((b) => b.batch_id === preferred) ? preferred : (latestAI || data.batches[0]).batch_id;
  await loadBatch(select.value);
}
async function loadBatch(batchId, keepReviewId) {
  const data = await api(`/api/batches/${encodeURIComponent(batchId)}`);
  state.batchId = batchId; state.batch = data.batch; state.packets = data.packets;
  renderSidebar();
  const selected = data.packets.find((p) => p.review_id === keepReviewId) || data.packets[0];
  if (selected) await loadPacket(selected.review_id);
}
function renderSidebar() {
  const isAIOnly = aiOnly();
  $("workspace-title").textContent = isAIOnly ? "AI 评审证据工作台" : "人工评审工作台";
  document.title = `TextPrison · ${isAIOnly ? "AI 评审" : "人工评审"}`;
  $("freeze-batch").hidden = isAIOnly;
  $("freeze-help").hidden = isAIOnly;
  $("human-guide").hidden = isAIOnly;
  $("ai-guide").hidden = !isAIOnly;
  const submitted = state.packets.filter((p) => ["submitted", "frozen"].includes(p.initial?.state)).length;
  const adjudicated = state.packets.filter((p) => p.adjudication?.state === "submitted").length;
  if (isAIOnly) {
    const progress = state.packets.reduce((total, packet) => {
      total.recorded += packet.ai_progress.recorded; total.completed += packet.ai_progress.completed;
      for (const [status, count] of Object.entries(packet.ai_progress.statuses)) total.statuses[status] = (total.statuses[status] || 0) + count;
      return total;
    }, {recorded: 0, completed: 0, statuses: {}});
    $("batch-progress").textContent = `${state.packets.length} 个候选 · ${aiProgressText(progress)}`;
  } else $("batch-progress").textContent = `独立初判 ${submitted}/${state.packets.length} · 最终裁决 ${adjudicated}/${state.packets.length}`;
  const list = $("packet-list"); list.replaceChildren();
  for (const packet of state.packets) {
    const node = button(packet.label, () => guarded(async () => { if (await abandonUnsaved()) await loadPacket(packet.review_id); }), "packet-button");
    if (state.packet?.review_id === packet.review_id) node.classList.add("active");
    const progress = isAIOnly ? aiProgressText(packet.ai_progress) : `初判：${statusNames[packet.initial.state]}${state.batch.state === "frozen" ? ` / 裁决：${statusNames[packet.adjudication.state]}` : ""}`;
    node.append(el("span", progress, "status"));
    list.append(node);
  }
  $("freeze-batch").disabled = isAIOnly || state.batch.state === "frozen" || submitted !== state.packets.length || !submitted;
  $("freeze-batch").textContent = state.batch.state === "frozen" ? "初判已冻结 · AI 已可见" : "冻结整批初判，查看 AI 证据";
  $("export-batch").disabled = false;
  $("refresh-batch").disabled = false;
}
async function loadPacket(reviewId) {
  const packet = await api(`/api/reviews/${encodeURIComponent(reviewId)}`);
  state.packet = packet;
  state.stage = packet.review_mode === "ai_only" ? null : packet.ai_revealed ? "adjudication" : "initial";
  const record = state.stage ? packet[state.stage] : null;
  state.revision = record?.revision || 0; state.review = record ? structuredClone(record.review) : null; state.dirty = false;
  notice(""); renderSidebar(); renderWorkspace();
}
function renderReading() {
  const grid = el("section", null, "reading-grid");
  const sources = el("article", null, "panel source-panel"); sources.append(el("h3", "任务与冻结来源"));
  sources.append(el("p", state.packet.task.prompt, "task-text"));
  const transforms = state.packet.task.allowed_transformations;
  if (transforms.length) { const list = el("ul"); transforms.forEach((text) => list.append(el("li", text))); sources.append(el("h4", "允许的转换"), list); }
  if (state.packet.task.output_contract) {
    const detail = el("details"); detail.append(el("summary", "输出要求与行为约束"));
    const contract = state.packet.task.output_contract;
    detail.append(el("pre", typeof contract === "string" ? contract : JSON.stringify(contract, null, 2), "document")); sources.append(detail);
  }
  if (state.packet.task.severity_rubric || state.packet.task.rubric) {
    const detail = el("details"); detail.append(el("summary", "本任务严重程度说明"));
    const rubric = state.packet.task.severity_rubric || state.packet.task.rubric;
    detail.append(el("pre", typeof rubric === "string" ? rubric : JSON.stringify(rubric, null, 2), "document")); sources.append(detail);
  }
  for (const source of state.packet.task.sources) {
    const block = el("section", null, "source-block"); block.append(el("div", source.id, "source-id"), el("pre", source.text, "document")); sources.append(block);
  }
  if (!state.packet.task.sources.length) sources.append(el("p", "此任务未提供来源。请据此判断来源覆盖情况。", "muted"));
  const candidate = el("article", null, "panel"); candidate.append(el("h3", "匿名候选"), el("pre", state.packet.candidate_text, "document"));
  candidate.append(el("p", `SHA-256 ${state.packet.artifact_hash}`, "hash"));
  if (state.packet.original_text) { const original = el("details"); original.append(el("summary", "改写前原文"), el("pre", state.packet.original_text, "document original")); candidate.append(original); }
  grid.append(sources, candidate); return grid;
}
function sourceReferences(item, parent) {
  const refs = el("div");
  const draw = () => {
    refs.replaceChildren();
    item.source_refs.forEach((ref, index) => {
      const block = el("div", null, "source-reference");
      block.append(field("来源 ID", ref.source_id, (value) => { ref.source_id = value; }, {options: [["", "选择来源"], ...state.packet.task.sources.map((source) => [source.id, source.id])]}));
      block.append(field("来源原文引文", ref.evidence, (value) => { ref.evidence = value; }, {placeholder: "复制对应来源的原文；支持、矛盾、保留、改变必须给出来源引文。"}));
      block.append(button("移除此证据", () => { item.source_refs.splice(index, 1); markDirty(); draw(); }, "quiet small")); refs.append(block);
    });
  };
  parent.append(el("h4", "来源证据"), refs, button("＋ 添加来源证据", () => { item.source_refs.push({source_id: state.packet.task.sources[0]?.id || "", evidence: ""}); markDirty(); draw(); }, "quiet small")); draw();
}
function judgment(item, type, index) {
  const block = el("fieldset", null, "judgment");
  block.append(el("legend", type === "claims" ? `事实声明 ${index + 1}` : `必需事实 ${item.id}`));
  if (type === "claims") block.append(field("声明全文（保留条件、模态和数量单位）", item.text, (value) => { item.text = value; }));
  else block.append(el("p", state.packet.task.required_facts.find((fact) => fact.id === item.id)?.text || item.id, "frozen-fact"));
  let typesPanel;
  const row = el("div", null, "row");
  row.append(field("判定", item.status, (value) => { item.status = value; if (typesPanel) typesPanel.open = errorStatuses.has(value); }, {options: type === "claims" ? claimOptions : factOptions}), field("严重程度", item.severity, (value) => { item.severity = value || null; }, {options: severityOptions})); block.append(row);
  item.error_types ||= [];
  typesPanel = el("details", null, "error-types"); typesPanel.open = errorStatuses.has(item.status);
  typesPanel.append(el("summary", "错误类型（已确认语义错误至少选择一项）"));
  const typesGrid = el("div", null, "type-options");
  for (const [key, label] of errorTypeOptions) {
    const choice = el("label", null, "check"); const input = el("input"); input.type = "checkbox"; input.checked = item.error_types.includes(key);
    input.addEventListener("change", () => { item.error_types = input.checked ? [...item.error_types, key] : item.error_types.filter((value) => value !== key); markDirty(); });
    choice.append(input, document.createTextNode(label)); typesGrid.append(choice);
  }
  typesPanel.append(typesGrid); block.append(typesPanel);
  block.append(field("候选原文引文", item.candidate_span, (value) => { item.candidate_span = value || null; }, {placeholder: "直接复制候选中的原文。缺失事实应留空。"}));
  sourceReferences(item, block);
  block.append(field("判定依据", item.justification, (value) => { item.justification = value; }, {placeholder: "说明引文如何支持此判定；缺失时指出缺少的必需事实。"}));
  if (type === "claims") block.append(button("移除此声明", () => { state.review.claims.splice(index, 1); markDirty(); renderForm(); }, "quiet danger small"));
  return block;
}
function renderForm() {
  const form = $("human-form"); form.replaceChildren();
  const title = state.stage === "initial" ? "独立初判" : "最终人工裁决";
  form.append(el("h2", title));
  if (state.stage === "adjudication") {
    form.append(el("p", "你可以参考上方 AI 证据作出裁决。冻结初判保持原样；本页保存独立的裁决版本。", "muted"));
    form.append(button("将我的初判复制到裁决草稿", async () => {
      if (state.dirty && !await confirmAction("用冻结初判替换当前未保存的裁决草稿？")) return;
      state.review = structuredClone(state.packet.initial.review); state.review.adjudication_reason = ""; delete state.review.summary; markDirty(); renderForm();
    }, "quiet"));
  }
  const coverage = el("section", null, "form-section");
  coverage.append(field("来源覆盖情况", state.review.source_coverage, (value) => { state.review.source_coverage = value; }, {options: [["", "请选择"], ["adequate", "充分：可以评价所给声明"], ["partial", "部分充分：仍有证据缺口"], ["insufficient", "不足：无法完成有意义的评价"]]}));
  coverage.append(field("来源覆盖说明", state.review.coverage_note, (value) => { state.review.coverage_note = value; }, {placeholder: "来源不足或冲突时，指出涉及的来源 ID 和缺少的信息。"})); form.append(coverage);
  const claims = el("section", null, "form-section"); const claimsHead = el("div", null, "section-head"); claimsHead.append(el("h3", "逐条事实声明"), button("＋ 添加声明", () => {
    state.review.claims.push({id: `human-${crypto.randomUUID()}`, text: "", status: "", candidate_span: null, severity: null, error_types: [], source_refs: [], justification: ""}); state.review.no_claims_confirmed = false; markDirty(); renderForm();
  }, "quiet")); claims.append(claimsHead);
  claims.append(el("p", "由你独立识别声明，系统不会用 AI 的声明列表填入初判。可以拆分、合并或删除自己添加的条目。", "help"));
  state.review.claims.forEach((item, index) => claims.append(judgment(item, "claims", index)));
  const noClaims = el("label", null, "check"); const checkbox = el("input"); checkbox.type = "checkbox"; checkbox.checked = state.review.no_claims_confirmed; checkbox.disabled = state.review.claims.length > 0;
  checkbox.addEventListener("change", () => { state.review.no_claims_confirmed = checkbox.checked; markDirty(); }); noClaims.append(checkbox, document.createTextNode("我已检查：候选不包含可评价的事实声明")); claims.append(noClaims); form.append(claims);
  const facts = el("section", null, "form-section"); facts.append(el("h3", "预先声明的必需事实"));
  state.review.required_facts.forEach((item, index) => facts.append(judgment(item, "required_facts", index)));
  if (!state.review.required_facts.length) facts.append(el("p", "本任务未预先声明必需事实。", "muted")); form.append(facts);
  const uncertain = el("section", null, "form-section"); const uncertainHead = el("div", null, "section-head"); uncertainHead.append(el("h3", "尚待澄清的项目"), button("＋ 添加不确定项", () => { state.review.uncertain_items.push({text: "", evidence_needed: ""}); markDirty(); renderForm(); }, "quiet")); uncertain.append(uncertainHead);
  state.review.uncertain_items.forEach((item, index) => {
    const block = el("fieldset", null, "judgment"); block.append(el("legend", `不确定项 ${index + 1}`), field("具体问题", item.text, (value) => { item.text = value; }), field("解决问题需要什么证据", item.evidence_needed, (value) => { item.evidence_needed = value; }), button("移除此项", () => { state.review.uncertain_items.splice(index, 1); markDirty(); renderForm(); }, "quiet small")); uncertain.append(block);
  }); form.append(uncertain);
  if (state.stage === "adjudication") form.append(field("裁决理由（提交必填）", state.review.adjudication_reason, (value) => { state.review.adjudication_reason = value; }, {placeholder: "说明采纳了哪些 AI 证据、如何处理分歧，以及修改或维持初判的原因。"}));
  const summary = state.review.summary;
  if (summary) form.append(el("p", `上次保存的派生汇总：${statusNames[summary.status] || summary.status} · 声明 ${state.review.claims.length} 条 · 必需事实 ${state.review.required_facts.length}/${summary.required_fact_total}。当前修改提交后重新计算。`, "summary-line"));
  const actions = el("div", null, "actions"); actions.append(button("保存草稿", () => guarded(() => save(false)), "quiet"), button(state.stage === "initial" ? "提交独立初判" : "提交最终裁决", () => guarded(() => save(true)), "primary"), button("查看修订历史", () => guarded(showHistory), "quiet"));
  const status = el("span", state.dirty ? "有未保存修改" : `已载入版本 ${state.revision} · ${statusNames[state.packet[state.stage].state]}`, "save-status"); status.id = "save-status"; actions.append(status); form.append(actions);
}
function renderAI() {
  const container = el("section"); container.append(el("h2", "AI 评审证据"), el("p", aiOnly() ? "各模型独立展示原始判断和运行状态。已完成表示返回了评审记录，不代表候选通过；模型一致也不构成人工金标准。" : "这些是各 AI 的原始判断，可能遗漏或误判。请对照来源作出自己的裁决；不采用多数票。", "ai-note"));
  if (!aiOnly()) {
    const initial = el("details", null, "panel initial-panel"); initial.append(el("summary", "查看已冻结的独立初判"), el("pre", JSON.stringify(state.packet.initial.review, null, 2), "json-evidence")); container.append(initial);
  }
  const grid = el("div", null, "judges-grid");
  for (const item of state.packet.ai_reviews) {
    const panel = el("article", null, "panel judge-panel"); panel.append(el("h3", item.judge_id));
    panel.append(el("p", `运行状态：${aiStatusNames[item.status || "completed"] || item.status}`, "tag"));
    if (item.provider || item.model) panel.append(el("p", [item.provider, item.model].filter(Boolean).join(" / "), "muted small"));
    const raw = el("details"); raw.append(el("summary", "完整原始记录 JSON"), el("pre", JSON.stringify(item, null, 2), "json-evidence"));
    const review = item.review;
    if (item.status && item.status !== "completed") {
      panel.append(el("p", `未获得有效评审 · ${item.status}`, "ai-note"), el("p", item.error || "本次评审未完成或未通过格式校验。该记录不提供可采用的判断，也不记作通过。", "task-text"));
      panel.append(raw); grid.append(panel); continue;
    }
    for (const [key, heading] of [["claims", "事实声明"], ["required_facts", "必需事实"], ["edits", "语义编辑"], ["uncertain_items", "不确定项"]]) {
      const entries = review[key]; if (!Array.isArray(entries) || !entries.length) continue;
      panel.append(el("h4", heading));
      for (const entry of entries) {
        const block = el("div", null, "ai-item");
        block.append(el("strong", `${entry.id || entry.fact_id || ""} ${entry.status || entry.semantic_category || ""}${entry.severity ? ` · ${entry.severity}` : ""}`));
        if (entry.text) block.append(el("p", entry.text));
        if (entry.candidate_span) block.append(el("p", `候选引文：${typeof entry.candidate_span === "string" ? entry.candidate_span : JSON.stringify(entry.candidate_span)}`));
        if (entry.justification) block.append(el("p", entry.justification));
        if (entry.error_types?.length) block.append(el("p", `错误类型：${entry.error_types.join(", ")}`));
        if (entry.evidence_needed) block.append(el("p", `需要的证据：${entry.evidence_needed}`));
        const refs = entry.source_evidence || entry.source_refs; if (refs?.length) block.append(el("pre", JSON.stringify(refs, null, 2)));
        panel.append(block);
      }
    }
    panel.append(raw); grid.append(panel);
  }
  if (!state.packet.ai_reviews.length) grid.append(el("p", aiOnly() ? "本候选尚无 AI 评审记录。刷新批次可查看新导入的结果。" : "本候选没有可用的 AI 评审；请在裁决理由中记录这一限制。", "muted"));
  container.append(grid); return container;
}
function renderWorkspace() {
  const workspace = $("workspace"); workspace.replaceChildren();
  const heading = el("div", null, "review-heading"); const title = el("div"); title.append(el("span", aiOnly() ? "AI-only · 模型证据" : state.packet.ai_revealed ? "第二阶段 · 参考 AI 后裁决" : "第一阶段 · 独立初判", "tag"), el("h2", state.packet.label), el("p", `${state.packet.task.profile} · ${state.packet.task.language}`, "muted"));
  heading.append(title, el("p", aiOnly() ? "直接展示 AI 结果 · 无人工评审阶段" : state.packet.ai_revealed ? "初判已冻结并独立保存" : "AI 结论与实验分组尚未揭示", "context-note")); workspace.append(heading, renderReading());
  if (state.packet.ai_revealed) workspace.append(renderAI());
  if (aiOnly()) return;
  const form = el("section", null, "panel review-form"); form.id = "human-form"; workspace.append(form); renderForm();
}
async function save(submit) {
  const result = await api(`/api/reviews/${state.packet.review_id}/${state.stage}`, {artifact_hash: state.packet.artifact_hash, expected_revision: state.revision, request_id: crypto.randomUUID(), submit, review: state.review});
  state.packet[state.stage] = result; state.revision = result.revision; state.review = structuredClone(result.review); state.dirty = false;
  const data = await api(`/api/batches/${encodeURIComponent(state.batchId)}`); state.batch = data.batch; state.packets = data.packets; renderSidebar(); renderForm();
  notice(`${submit ? "已提交" : "草稿已保存"}，版本 ${result.revision}。${submit ? ` 派生状态：${statusNames[result.review.summary.status]}。` : ""}`);
}
async function showHistory() {
  const data = await api(`/api/reviews/${state.packet.review_id}/history`); const content = $("history-content"); content.replaceChildren();
  for (const item of data.history) {
    const detail = el("details"); detail.append(el("summary", `${item.stage === "initial" ? "初判" : "裁决"} v${item.revision} · ${item.action} · ${item.created_at}`), el("pre", JSON.stringify(item.review, null, 2), "json-evidence")); content.append(detail);
  }
  if (!data.history.length) content.append(el("p", "尚无保存记录。")); $("history-dialog").showModal();
}
$("batch-select").addEventListener("change", () => guarded(async () => { if (await abandonUnsaved()) await loadBatch($("batch-select").value); else $("batch-select").value = state.batchId; }));
$("refresh-batch").addEventListener("click", () => guarded(async () => { if (await abandonUnsaved()) await loadBatch(state.batchId, state.packet?.review_id); }));
$("freeze-batch").addEventListener("click", () => guarded(async () => {
  if (state.dirty) throw new Error("请先保存或提交当前修改，再冻结批次。");
  if (!await confirmAction("冻结后，本批次全部独立初判将无法修改，AI 证据随后可见。继续冻结？")) return;
  const expected_revisions = Object.fromEntries(state.packets.map((packet) => [packet.review_id, packet.initial.revision]));
  await api(`/api/batches/${encodeURIComponent(state.batchId)}/freeze`, {expected_revisions}); await loadBatch(state.batchId, state.packet?.review_id); notice("整批初判已冻结。现在可以查看 AI 证据并填写最终裁决。");
}));
$("export-batch").addEventListener("click", () => guarded(async () => {
  const data = await api(`/api/batches/${encodeURIComponent(state.batchId)}/export`); const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type: "application/json"}));
  const anchor = el("a"); anchor.href = url; anchor.download = `textprison-${state.batchId.replace(/[^a-zA-Z0-9_-]/g, "_")}-review.json`; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  notice(aiOnly() ? "已导出当前 AI 评审、运行状态和来源证据。本批次没有人工初判或裁决记录。" : "已导出当前保存版本。未冻结批次的导出仍隐藏 AI 结果；未保存的表单修改不在导出中。");
}));
$("stop-service").addEventListener("click", () => guarded(async () => {
  if (!await abandonUnsaved() || !await confirmAction("停止本地评审服务？已保存的数据会保留，可在重启后继续。")) return;
  await api("/api/shutdown", {}); state.dirty = false; notice("服务已停止。已保存的草稿和评审保留在数据库中。");
}));
$("close-history").addEventListener("click", () => $("history-dialog").close());
window.addEventListener("beforeunload", (event) => { if (state.dirty) { event.preventDefault(); event.returnValue = ""; } });
guarded(async () => { const session = await api("/api/session"); state.token = session.token; await loadBatches(); });
