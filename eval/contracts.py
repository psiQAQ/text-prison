"""Versioned experiment contracts; measurements are never inferred from style checks."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


EVAL_ROOT = Path(__file__).resolve().parent
SCHEMA_ROOT = EVAL_ROOT / "schemas"
PUBLIC_TASK_FIELDS = (
    "id", "scenario_id", "profile", "language", "prompt", "sources",
    "required_facts", "allowed_transformations", "output_contract", "rubric",
    "synthetic", "executable",
)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON number: {value}")


def _finite_tree(value: Any, location: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Non-finite number at {location}")
    if isinstance(value, dict):
        for key, item in value.items():
            _finite_tree(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _finite_tree(item, f"{location}[{index}]")


def loads_json(text: str) -> Any:
    """Parse JSON without duplicate keys, NaN, Infinity, or overflow-to-infinity."""
    value = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    _finite_tree(value)
    return value


def load_json(path: str | Path) -> Any:
    return loads_json(Path(path).read_text(encoding="utf-8"))


def canonical_hash(value: Any) -> str:
    _finite_tree(value)
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def schema(name: str) -> dict[str, Any]:
    if name not in {"run-v0.1", "run-v0.2", "review-v0.2", "task-v0.2", "human-review-v0.2"}:
        raise ValueError(f"Unknown local schema: {name}")
    return load_json(SCHEMA_ROOT / f"{name}.schema.json")


def _validate_schema(value: Any, name: str) -> None:
    _finite_tree(value)
    errors = sorted(Draft202012Validator(schema(name)).iter_errors(value), key=lambda error: str(list(error.path)))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "$"
        raise ValueError(f"{name} {location}: {error.message}")


def _unique_ids(records: list[dict[str, Any]], field: str, label: str) -> set[str]:
    ids = [record[field] for record in records]
    if len(set(ids)) != len(ids):
        raise ValueError(f"Duplicate {label} IDs")
    return set(ids)


def validate_task(task: dict[str, Any]) -> dict[str, Any]:
    _validate_schema(task, "task-v0.2")
    _unique_ids(task["sources"], "id", "source")
    _unique_ids(task["required_facts"], "id", "required fact")
    if not task["sources"] or not task["required_facts"]:
        raise ValueError("Task must declare sources and required facts before generation")
    return deepcopy(task)


def model_visible_task(task: dict[str, Any]) -> dict[str, Any]:
    """Whitelist, rather than blacklist, all data allowed in a writer/judge packet."""
    validate_task(task)
    return {key: deepcopy(task[key]) for key in PUBLIC_TASK_FIELDS if key in task}


def load_tasks(root: str | Path | None = None) -> list[dict[str, Any]]:
    folder = Path(root) if root is not None else EVAL_ROOT / "tasks"
    tasks = [validate_task(load_json(path)) for path in sorted(folder.glob("*.json"))]
    _unique_ids(tasks, "id", "task")
    return tasks


def load_calibration_packets(root: str | Path | None = None) -> list[dict[str, Any]]:
    """Load public candidates only; private mutation labels are never included."""
    folder = Path(root) if root is not None else EVAL_ROOT / "calibration"
    packets = []
    for path in sorted(folder.glob("*.json")):
        value = load_json(path)
        task = model_visible_task(value["task"])
        candidate = value["candidate_text"]
        if not isinstance(candidate, str):
            raise ValueError(f"Calibration candidate must be text: {path.name}")
        packet = {"review_id": value["review_id"], "batch_id": value["batch_id"],
                  "artifact_hash": text_hash(candidate), "candidate_text": candidate, "task": task}
        if "original_text" in value:
            packet["original_text"] = value["original_text"]
        packets.append(packet)
    _unique_ids(packets, "review_id", "calibration review")
    return packets


def validate_run(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("schema_version") != "0.2":
        raise ValueError("validate_run expects v0.2; use normalize_run for legacy records")
    _validate_schema(record, "run-v0.2")
    if record["retry_of"] == record["attempt_id"]:
        raise ValueError("retry_of cannot name the current attempt")
    usage = record["usage"]
    if usage["coverage"] == "complete" and (usage["input_total"] is None or usage["output_total"] is None):
        raise ValueError("Complete usage requires known input/output totals")
    if record["outcomes"]["semantic_status"] != "not_evaluated" and not record["review_refs"]:
        raise ValueError("A semantic outcome requires a separate review reference")
    return deepcopy(record)


def normalize_run(record: dict[str, Any]) -> dict[str, Any]:
    """Read v0.1 without rewriting its file or claiming new measurements occurred."""
    if record.get("schema_version") == "0.2":
        return validate_run(record)
    if record.get("schema_version") != "0.1":
        raise ValueError(f"Unsupported run schema version: {record.get('schema_version')}")
    _validate_schema(record, "run-v0.1")
    result = deepcopy(record)
    result.update({"schema_version": "0.2", "track": "legacy", "assignment_id": record["run_id"],
                   "attempt_id": record["run_id"], "retry_of": None, "artifact_refs": [], "review_refs": [],
                   "legacy_original": deepcopy(record)})
    result["phase"] = record.get("phase", "unknown")
    result["cost_scope"] = {"writer": "production_writer", "executor": "downstream_executor",
                            "reader": "evaluation_only", "trigger": "evaluation_only", "judge": "evaluation_only"}.get(result["phase"], "unknown")
    # A v0.1 status without an independent review is historical, not v0.2 evidence.
    result["outcomes"]["semantic_status"] = "not_evaluated"
    result["outcomes"]["critical_errors"] = None
    usage = result["usage"]
    if usage["coverage"] == "complete" and (usage["input_total"] is None or usage["output_total"] is None):
        usage["coverage"] = "partial" if usage["input_total"] is not None or usage["output_total"] is not None else "unknown"
    for key in ("rule_hash", "source_hash", "artifact_hash"):
        value = result.get(key)
        if value is not None and (len(value) != 64 or any(char not in "0123456789abcdef" for char in value)):
            result[key] = None
    result["provenance"] = {"converted_from": "0.1", "conversion": "lossless-original-with-unmeasured-v0.2-fields",
                            "warning": "Legacy original is preserved; absent metadata and semantic review remain unknown."}
    return validate_run(result)


def derive_review_summary(review: dict[str, Any], task: dict[str, Any] | None = None) -> dict[str, Any]:
    claims = Counter(item["status"] for item in review["claims"])
    facts = Counter(item["status"] for item in review["required_facts"])
    expected_ids = {item["id"] for item in task["required_facts"]} if task is not None else {item["fact_id"] for item in review["required_facts"]}
    reviewed_ids = {item["fact_id"] for item in review["required_facts"]}
    unreviewed = len(expected_ids - reviewed_ids)
    errors = [item for item in review["claims"] if item["status"] in {"contradicted", "unsupported"}]
    errors += [item for item in review["required_facts"] if item["status"] in {"missing", "altered"}]
    errors += [item for item in review["edits"] if item["severity"] != "style_only"]
    error_types: Counter[str] = Counter()
    for item in errors:
        error_types.update(set(item.get("error_types", [item.get("semantic_category", "other")])))
    meaningful = bool(review["claims"] or review["required_facts"] or review["edits"])
    unresolved = bool(claims["unassessable"] or facts["unassessable"] or unreviewed or review["uncertain_items"])
    complete = meaningful and not unresolved and review["source_coverage"]["status"] == "adequate"
    if errors:
        status = "failed"
    elif not meaningful or review["source_coverage"]["status"] == "insufficient":
        status = "not_evaluated"
    elif complete:
        status = "passed"
    else:
        status = "uncertain"
    return {"status": status,
            "claims": {"total": len(review["claims"]), **{key: claims[key] for key in ("supported", "contradicted", "unsupported", "unassessable")}},
            "required_facts": {"total": len(expected_ids), **{key: facts[key] for key in ("preserved", "missing", "altered", "unassessable")}, "unreviewed": unreviewed},
            "semantic_errors": len(errors), "critical_errors": sum(item["severity"] == "critical" for item in errors),
            "review_complete": complete, "error_types": dict(sorted(error_types.items()))}


def _quote_exists(quote: str | None, text: str | None, label: str) -> None:
    if quote is not None and (not quote or (text is not None and quote not in text)):
        raise ValueError(f"{label} must be a nonempty exact quote from the frozen text")


def validate_review(review: dict[str, Any], task: dict[str, Any] | None = None,
                    candidate_text: str | None = None, original_text: str | None = None) -> dict[str, Any]:
    _validate_schema(review, "review-v0.2")
    result = deepcopy(review)
    _unique_ids(result["claims"], "id", "claim")
    fact_ids = _unique_ids(result["required_facts"], "fact_id", "reviewed required fact")
    _unique_ids(result["edits"], "id", "edit")
    _unique_ids(result["uncertain_items"], "id", "uncertain item")
    source_texts = None
    if task is not None:
        validate_task(task)
        expected = {fact["id"] for fact in task["required_facts"]}
        if fact_ids != expected:
            raise ValueError(f"Required fact IDs must match task inventory; missing={sorted(expected-fact_ids)}, extra={sorted(fact_ids-expected)}")
        source_texts = {source["id"]: source["text"] for source in task["sources"]}
        if set(result["source_coverage"]["affected_source_ids"]) - source_texts.keys():
            raise ValueError("Coverage references unknown source IDs")
    for collection in ("claims", "required_facts", "edits"):
        for item in result[collection]:
            _quote_exists(item["candidate_span"], candidate_text, "candidate_span")
            if collection == "edits":
                _quote_exists(item["original_span"], original_text, "original_span")
            else:
                status = item["status"]
                if collection == "claims" and item["candidate_span"] is None:
                    raise ValueError("Every extracted claim requires a candidate quote")
                if status == "preserved" and item["candidate_span"] is None:
                    raise ValueError("Preserved facts require candidate evidence")
                if status == "missing" and item["candidate_span"] is not None:
                    raise ValueError("Missing facts must use a null candidate_span")
                if status in {"contradicted", "unsupported", "missing", "altered"}:
                    if item["severity"] not in {"critical", "major", "minor"} or not item["error_types"]:
                        raise ValueError("Confirmed semantic errors require semantic severity and error_types")
                elif item["severity"] is not None or item["error_types"]:
                    raise ValueError("Supported, preserved, and unresolved items cannot claim confirmed errors")
            for evidence in item["source_evidence"]:
                if source_texts is not None and evidence["source_id"] not in source_texts:
                    raise ValueError(f"Unknown source ID: {evidence['source_id']}")
                source_text = source_texts[evidence["source_id"]] if source_texts is not None else None
                _quote_exists(evidence["span"], source_text, "source span")
            if item.get("status") in {"supported", "contradicted", "preserved", "altered"} and not item["source_evidence"]:
                raise ValueError("Source-supported or contradicted judgments require source evidence")
    result["summary"] = derive_review_summary(result, task)
    return result
