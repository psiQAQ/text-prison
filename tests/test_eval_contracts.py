from copy import deepcopy
import json
from pathlib import Path

import pytest

from eval.contracts import (
    canonical_hash, derive_review_summary, load_calibration_packets, load_json,
    load_tasks, loads_json, model_visible_task, normalize_run, schema,
    validate_review, validate_run,
)
from eval.tasks.private.verifier import prepare_workspace, verify_execution


ROOT = Path(__file__).resolve().parents[1]


def basic_task():
    return {"id": "t", "scenario_id": "s", "profile": "research", "language": "en",
            "prompt": "Preserve the stated condition.", "sources": [{"id": "s1", "text": "The value may be 2 s."}],
            "required_facts": [{"id": "r1", "text": "The value may be 2 s."}],
            "allowed_transformations": [], "output_contract": {},
            "rubric": {"critical": ["Modality change"], "major": ["Omission"], "minor": [], "style_only": []}}


def supported_review():
    evidence = [{"source_id": "s1", "span": "may be 2 s"}]
    shared = {"candidate_span": "may be 2 s", "source_evidence": evidence,
              "justification": "The qualifier and value are retained.", "severity": None, "error_types": []}
    return {"review_version": "0.2", "source_coverage": {"status": "adequate", "affected_source_ids": [], "note": ""},
            "claims": [{"id": "c1", "text": "The value may be 2 s.", "status": "supported", **deepcopy(shared)}],
            "required_facts": [{"fact_id": "r1", "status": "preserved", **deepcopy(shared)}],
            "edits": [], "uncertain_items": []}


def legacy_run():
    return {"schema_version": "0.1", "run_id": "old", "task_id": "t", "scenario_id": "s", "arm": "A",
            "host": "test", "model": "test", "profile": "research", "language": "en", "status": "completed",
            "usage": {"coverage": "unknown", "input_total": None, "output_total": None, "raw_log": None},
            "outcomes": {"semantic_status": "passed", "agent_success": None, "trigger_observed": None}}


@pytest.mark.parametrize("text", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}'])
def test_strict_json_rejects_lossy_input(text):
    with pytest.raises(ValueError):
        loads_json(text)


def test_hash_stable_and_json_unicode_preserved():
    assert canonical_hash({"字": 2, "x": 1}) == canonical_hash({"x": 1, "字": 2})
    assert loads_json('{"text":"中\\u2028文"}')["text"] == "中\u2028文"


def test_legacy_conversion_is_explicit_and_preserves_original():
    old = legacy_run()
    before = deepcopy(old)
    new = normalize_run(old)
    assert old == before
    assert new["legacy_original"] == before
    assert new["schema_version"] == "0.2"
    assert new["phase"] == new["cost_scope"] == "unknown"
    assert new["track"] == "legacy"
    assert new["outcomes"]["semantic_status"] == "not_evaluated"
    assert new["usage"]["input_total"] is None


def test_legacy_complete_missing_usage_is_not_promoted_to_zero():
    old = legacy_run()
    old["phase"] = "writer"
    old["usage"].update(coverage="complete", input_total=17)
    new = normalize_run(old)
    assert new["cost_scope"] == "production_writer"
    assert new["usage"]["coverage"] == "partial"
    assert new["usage"]["output_total"] is None


def test_v02_new_run_requires_evidence_and_measured_usage():
    new = normalize_run(legacy_run())
    new["track"] = "product_native"
    with pytest.raises(ValueError):
        validate_run(new)
    new.update(phase="writer", cost_scope="production_writer")
    new["usage"]["coverage"] = "complete"
    with pytest.raises(ValueError, match="Complete usage"):
        validate_run(new)
    new["usage"].update(input_total=10, output_total=2)
    new["outcomes"]["semantic_status"] = "passed"
    with pytest.raises(ValueError, match="review reference"):
        validate_run(new)


def test_run_schema_alias_matches_versioned_file():
    assert load_json(ROOT / "eval/run.schema.json") == schema("run-v0.2")
    assert schema("run-v0.1")["properties"]["schema_version"]["const"] == "0.1"


def test_review_status_and_counts_are_derived_not_accepted_on_trust():
    review = supported_review()
    review["summary"] = derive_review_summary(review, basic_task())
    review["summary"]["status"] = "failed"
    checked = validate_review(review, basic_task(), "The value may be 2 s.")
    assert checked["summary"]["status"] == "passed"
    assert review["summary"]["status"] == "failed"


def test_missing_required_fact_cannot_be_labeled_passed():
    review = supported_review()
    review["required_facts"] = []
    assert derive_review_summary(review, basic_task())["status"] == "uncertain"
    with pytest.raises(ValueError, match="Required fact IDs"):
        validate_review(review, basic_task())


@pytest.mark.parametrize("mutation", ["wrong_quote", "unknown_source", "duplicate_claim", "false_error", "unscored_error"])
def test_review_evidence_failures_are_rejected(mutation):
    review = supported_review()
    if mutation == "wrong_quote":
        review["claims"][0]["candidate_span"] = "always 2 s"
    elif mutation == "unknown_source":
        review["claims"][0]["source_evidence"][0]["source_id"] = "s99"
    elif mutation == "duplicate_claim":
        review["claims"].append(deepcopy(review["claims"][0]))
    elif mutation == "false_error":
        review["claims"][0]["severity"] = "critical"
    else:
        review["claims"][0]["status"] = "contradicted"
    with pytest.raises(ValueError):
        validate_review(review, basic_task(), "The value may be 2 s.")


def test_semantic_error_and_uncertainty_have_separate_statuses():
    review = supported_review()
    fact = review["required_facts"][0]
    fact.update(status="missing", candidate_span=None, severity="major", error_types=["required_omission"])
    assert validate_review(review, basic_task(), "The value may be 2 s.")["summary"]["status"] == "failed"
    fact.update(status="unassessable", severity=None, error_types=[])
    assert validate_review(review, basic_task(), "The value may be 2 s.")["summary"]["status"] == "uncertain"
    review["source_coverage"]["status"] = "insufficient"
    assert validate_review(review, basic_task(), "The value may be 2 s.")["summary"]["status"] == "not_evaluated"


def test_task_and_calibration_packets_do_not_contain_private_truth():
    tasks = load_tasks()
    assert {(task["profile"], task["language"]) for task in tasks} == {
        ("explanation", "zh"), ("procedure", "en"), ("research", "en"), ("agent-spec", "zh")}
    assert len({task["scenario_id"] for task in tasks}) == 4
    polluted = deepcopy(tasks[0])
    polluted.update(private={"answer": "secret"}, reference_output="secret", expected_mutation="secret")
    public = model_visible_task(polluted)
    assert "secret" not in json.dumps(public)
    packets = load_calibration_packets()
    assert len(packets) == 12
    assert sum(packet["task"]["language"] == "zh" for packet in packets) == 6
    assert len({packet["task"]["scenario_id"] for packet in packets}) == 6
    assert all(len(packet["artifact_hash"]) == 64 for packet in packets)
    text = json.dumps(packets)
    assert "designed_variant" not in text and "designed_error_types" not in text and "human_initial_status" not in text


def reference_execution(task_id, tmp_path):
    workspace = tmp_path / task_id
    hashes = prepare_workspace(task_id, workspace)
    outputs = load_json(ROOT / "eval/tasks/private/reference_outputs.json")["executions"][task_id]
    events = []
    for relative, value in outputs.items():
        output = workspace / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        events.append({"tool": "write_file", "path": relative, "allowed": True})
    return workspace, hashes, events


@pytest.mark.parametrize("task_id", ["procedure-en-01", "agent-spec-zh-01"])
def test_reference_output_passes_independent_verifier_without_claiming_human_acceptance(task_id, tmp_path):
    workspace, hashes, events = reference_execution(task_id, tmp_path)
    result = verify_execution(task_id, workspace, events=events, initial_hashes=hashes)
    assert result["success"] is True
    assert result["human_validation_status"] == "pending"


@pytest.mark.parametrize("defect", ["wrong_unit", "wrong_json_type", "changed_input", "extra_file", "outside_attempt", "missing_trace", "budget"])
def test_verifier_rejects_declared_failures_or_marks_missing_evidence(defect, tmp_path):
    workspace, hashes, events = reference_execution("procedure-en-01", tmp_path)
    output = workspace / "output/config.json"
    if defect in {"wrong_unit", "wrong_json_type"}:
        value = load_json(output)
        value["timeout_ms"] = 2.5 if defect == "wrong_unit" else 2500.0
        output.write_text(json.dumps(value), encoding="utf-8")
    elif defect == "changed_input":
        original = workspace / "input/config.json"
        original.write_text(original.read_text(encoding="utf-8") + " ", encoding="utf-8")
    elif defect == "extra_file":
        (workspace / "unexpected.txt").write_text("extra", encoding="utf-8")
    elif defect == "outside_attempt":
        events.append({"tool": "write_file", "path": "../escape.json", "allowed": False})
    elif defect == "missing_trace":
        events = None
    result = verify_execution("procedure-en-01", workspace, events=events, initial_hashes=hashes, budget_ok=defect != "budget")
    assert result["success"] is (None if defect == "missing_trace" else False)


def test_agent_selection_requires_both_readiness_and_approval(tmp_path):
    workspace, hashes, events = reference_execution("agent-spec-zh-01", tmp_path)
    path = workspace / "output/plan.json"
    value = load_json(path)
    value.update(selected_ids=["q-06", "q-01", "q-02"], deferred_ids=["q-03", "q-04", "q-05"])
    path.write_text(json.dumps(value), encoding="utf-8")
    assert verify_execution("agent-spec-zh-01", workspace, events=events, initial_hashes=hashes)["success"] is False


def test_control_file_is_the_only_setup_exception(tmp_path):
    workspace = tmp_path / "prepared"
    (workspace / ".pi").mkdir(parents=True)
    (workspace / ".pi/settings.json").write_text('{"retry":{"enabled":false},"compaction":{"enabled":false}}', encoding="utf-8")
    hashes = prepare_workspace("procedure-en-01", workspace)
    assert ".pi/settings.json" in hashes
    (workspace / ".pi/extra.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        prepare_workspace("procedure-en-01", workspace)
