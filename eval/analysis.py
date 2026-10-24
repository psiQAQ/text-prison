"""Descriptive v0.2 metrics with explicit denominators and missingness.

These functions do not turn four synthetic scenarios into a powered experiment,
infer human acceptance, or calculate agreement between unaligned extracted claims.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import math
from statistics import mean
from typing import Any, Iterable

from eval.contracts import derive_review_summary


def ratio(numerator: int | float | None, denominator: int | float, *, assessed: int | float | None = None) -> dict[str, Any]:
    if denominator < 0 or (numerator is not None and numerator < 0):
        raise ValueError("Metric counts cannot be negative")
    value = numerator / denominator if numerator is not None and denominator else None
    return {"value": value, "numerator": numerator, "denominator": denominator,
            "coverage": assessed / denominator if assessed is not None and denominator else None,
            "status": "defined" if value is not None else ("undefined" if denominator == 0 else "not_evaluated")}


def as_semantic_review(review: dict[str, Any]) -> dict[str, Any]:
    """Adapt human storage for analysis without overwriting its independent record."""
    if isinstance(review.get("source_coverage"), dict):
        return deepcopy(review)
    result: dict[str, Any] = {"review_version": "0.2", "source_coverage": {
        "status": review["source_coverage"], "affected_source_ids": [], "note": review.get("coverage_note", "")},
        "claims": [], "required_facts": [], "edits": [], "uncertain_items": []}
    for name in ("claims", "required_facts"):
        for item in review.get(name, []):
            failed = item["status"] in {"contradicted", "unsupported", "missing", "altered"}
            converted = {"candidate_span": item.get("candidate_span"), "status": item["status"],
                         "severity": item.get("severity"), "justification": item.get("justification", ""),
                         "source_evidence": [{"source_id": evidence["source_id"], "span": evidence.get("evidence") or None}
                                             for evidence in item.get("source_refs", [])],
                         "error_types": item.get("error_types") or (["other"] if failed else [])}
            if name == "claims":
                converted.update({"id": item["id"], "text": item["text"]})
            else:
                converted["fact_id"] = item.get("fact_id", item.get("id"))
            result[name].append(converted)
    for index, item in enumerate(review.get("uncertain_items", [])):
        result["uncertain_items"].append({"id": item.get("id", f"u{index + 1}"),
                                          "affected_ids": item.get("affected_ids", []),
                                          "evidence_needed": item["evidence_needed"]})
    return result


def semantic_metrics(review: dict[str, Any] | None, task: dict[str, Any] | None = None) -> dict[str, Any]:
    if review is None:
        return {"status": "not_evaluated", "fsp_verified": None, "fsp_possible": None,
                "claim_determined_coverage": None, "rfr": None, "rfr_possible": None,
                "required_determined_coverage": None, "critical_present": None,
                "review_complete": False, "counts": None, "error_types": []}
    normalized = as_semantic_review(review)
    summary = derive_review_summary(normalized, task)
    claims, facts = summary["claims"], summary["required_facts"]
    n, s, q = claims["total"], claims["supported"], claims["unassessable"]
    r, k, u = facts["total"], facts["preserved"], facts["unassessable"] + facts["unreviewed"]
    unresolved_severity = any(item.get("severity") is None and item.get("status") in {"contradicted", "unsupported", "missing", "altered"}
                              for name in ("claims", "required_facts") for item in normalized[name])
    complete = summary["review_complete"] and not unresolved_severity
    critical = True if summary["critical_errors"] else (False if complete else None)
    return {"status": summary["status"], "fsp_verified": ratio(s, n, assessed=n-q),
            "fsp_possible": ratio(s+q, n, assessed=n-q), "claim_determined_coverage": ratio(n-q, n, assessed=n-q),
            "rfr": ratio(k, r, assessed=r-u), "rfr_possible": ratio(k+u, r, assessed=r-u),
            "required_determined_coverage": ratio(r-u, r, assessed=r-u), "critical_present": critical,
            "review_complete": complete, "counts": summary, "error_types": sorted(summary["error_types"])}


def scenario_macro(rows: Iterable[dict[str, Any]], value_key: str) -> dict[str, Any]:
    """Average repeats within scenario first; missing values remain unmeasured."""
    groups: dict[str, list[float | None]] = defaultdict(list)
    for row in rows:
        scenario_id = row.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id:
            raise ValueError("Scenario macro requires a nonempty scenario_id for every assignment")
        value = row.get(value_key)
        if isinstance(value, dict):
            value = value.get("value")
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
            raise ValueError(f"Invalid numeric metric: {value_key}")
        groups[scenario_id].append(value)
    scenarios = []
    for scenario_id, values in sorted(groups.items()):
        known = [value for value in values if value is not None]
        scenarios.append({"scenario_id": scenario_id, "value": mean(known) if known else None,
                          "assigned": len(values), "measured": len(known),
                          "coverage": len(known)/len(values)})
    known_scenarios = [item["value"] for item in scenarios if item["value"] is not None]
    return {"value": mean(known_scenarios) if known_scenarios else None,
            "scenario_denominator": len(scenarios), "scenarios_measured": len(known_scenarios),
            "coverage": len(known_scenarios)/len(scenarios) if scenarios else None,
            "scenarios": scenarios, "weighting": "equal scenario; equal observed assignments within scenario",
            "inference": "descriptive only; no confidence interval or population claim"}


def summarize_reviews(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Include a row with review=None for every assigned but unreviewed artifact.

    Caller must group by experimental track, arm, reviewer and review stage first.
    Mixing initial human labels with adjudication or AI labels is not supported.
    """
    for key in ("track", "arm", "reviewer_id", "review_stage"):
        values = {record[key] for record in records if record.get(key) is not None}
        if len(values) > 1:
            raise ValueError(f"Summarize homogeneous {key} groups separately")
    rows = [{"scenario_id": record["scenario_id"], **semantic_metrics(record.get("review"), record.get("task"))}
            for record in records]
    total = len(rows)
    critical = sum(row["critical_present"] is True for row in rows)
    unknown = sum(row["critical_present"] is None for row in rows)
    error_types = Counter(error_type for row in rows for error_type in set(row["error_types"]))
    for row in rows:
        row["critical_lower"] = 1.0 if row["critical_present"] is True else 0.0
        row["critical_upper"] = 0.0 if row["critical_present"] is False else 1.0
    keys = ("fsp_verified", "fsp_possible", "claim_determined_coverage", "rfr", "rfr_possible", "required_determined_coverage")
    return {"assigned_artifacts": total, "reviews_supplied": sum(record.get("review") is not None for record in records),
            "completed_review_coverage": ratio(sum(row["review_complete"] for row in rows), total, assessed=total),
            "macro": {key: scenario_macro(rows, key) for key in keys},
            "critical_prevalence": {"verified_lower": ratio(critical, total, assessed=total-unknown),
                                    "possible_upper": ratio(critical+unknown, total, assessed=total-unknown),
                                    "macro_lower": scenario_macro(rows, "critical_lower"),
                                    "macro_upper": scenario_macro(rows, "critical_upper")},
            "artifacts_by_error_type": dict(sorted(error_types.items())),
            "statuses": dict(Counter(row["status"] for row in rows)), "artifacts": rows,
            "note": "Possible bounds describe unresolved judgments, not statistical confidence intervals."}


def _first_attempts(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        groups[run["assignment_id"]].append(run)
    originals = []
    for assignment, attempts in groups.items():
        first = [attempt for attempt in attempts if attempt.get("retry_of") is None]
        if len(first) != 1:
            raise ValueError(f"Assignment {assignment} must retain exactly one original attempt")
        originals.append(first[0])
    return originals


def summarize_execution(runs: list[dict[str, Any]]) -> dict[str, Any]:
    attempts = [run for run in runs if run.get("phase") == "executor"]
    first = _first_attempts(attempts)
    rows = []
    for run in first:
        outcome = run.get("outcomes", {}).get("agent_success")
        if run["status"] in {"failed", "timeout", "interrupted"}:
            outcome = False
        elif run["status"] in {"not_run", "blocked"}:
            outcome = None
        if type(outcome) not in {bool, type(None)}:
            raise ValueError("agent_success must be boolean or null")
        rows.append({"scenario_id": run["scenario_id"], "assignment_id": run["assignment_id"],
                     "success": outcome, "success_observed": float(outcome) if outcome is not None else None,
                     "success_lower": 1.0 if outcome is True else 0.0,
                     "success_upper": 0.0 if outcome is False else 1.0})
    success = sum(row["success"] is True for row in rows)
    unknown = sum(row["success"] is None for row in rows)
    n = len(rows)
    return {"assigned": n, "attempts_including_retries": len(attempts), "successes": success, "unknown": unknown,
            "first_complete_success_verified": ratio(success, n, assessed=n-unknown),
            "first_complete_success_possible": ratio(success+unknown, n, assessed=n-unknown),
            "scenario_macro_verified": scenario_macro(rows, "success_lower"),
            "scenario_macro_possible": scenario_macro(rows, "success_upper"),
            "scenario_macro_observed": scenario_macro(rows, "success_observed"), "assignments": rows,
            "policy": "Original assigned attempt only; retained retries do not replace failures."}


def ppv(base_rate: float, tpr: float | None, fpr: float | None) -> float | None:
    for value in (base_rate, tpr, fpr):
        if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1):
            raise ValueError("Base rate, TPR and FPR must lie in [0,1]")
    if tpr is None or fpr is None:
        return None
    denominator = base_rate*tpr + (1-base_rate)*fpr
    return base_rate*tpr/denominator if denominator else None


def summarize_triggers(records: list[dict[str, Any]], base_rates: tuple[float, ...] = (0.01, 0.05, 0.1, 0.5)) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    routing_known = routing_correct = end_correct = end_unknown = 0
    observed_total = labeled_total = positive_total = 0
    for row in records:
        expected = row.get("expected_trigger")
        observed = row.get("trigger_observed", row.get("outcomes", {}).get("trigger_observed"))
        if type(expected) not in {bool, type(None)} or type(observed) not in {bool, type(None)}:
            raise ValueError("Trigger labels and observations must be boolean or null")
        observed_total += observed is not None
        if expected is None:
            counts["unlabeled"] += 1
            continue
        labeled_total += 1
        positive_total += expected
        if observed is None:
            counts["unknown_positive" if expected else "unknown_negative"] += 1
        else:
            counts[("tp" if observed else "fn") if expected else ("fp" if observed else "tn")] += 1
        if not expected:
            continue
        expected_profiles = row.get("expected_profiles")
        actual_profiles = row.get("observed_profiles")
        expected_language, actual_language = row.get("expected_language"), row.get("observed_language")
        known_route = (expected_profiles is not None and actual_profiles is not None and
                       expected_language is not None and actual_language is not None)
        route_ok = known_route and set(expected_profiles) == set(actual_profiles) and expected_language == actual_language
        if observed is True:
            routing_known += known_route
            routing_correct += route_ok
        end_correct += observed is True and route_ok
        end_unknown += observed is None or (observed is True and not known_route)
    tp, fn, fp, tn = (counts[key] for key in ("tp", "fn", "fp", "tn"))
    up, un = counts["unknown_positive"], counts["unknown_negative"]
    tpr, fpr = ratio(tp, tp+fn, assessed=tp+fn), ratio(fp, fp+tn, assessed=fp+tn)
    tpr_low, tpr_high = ratio(tp, tp+fn+up, assessed=tp+fn), ratio(tp+up, tp+fn+up, assessed=tp+fn)
    fpr_low, fpr_high = ratio(fp, fp+tn+un, assessed=fp+tn), ratio(fp+un, fp+tn+un, assessed=fp+tn)
    return {"total": len(records), "counts": {key: counts[key] for key in ("tp", "fp", "fn", "tn", "unknown_positive", "unknown_negative", "unlabeled")},
            "observation_coverage": ratio(observed_total, len(records), assessed=len(records)),
            "intent_label_coverage": ratio(labeled_total, len(records), assessed=len(records)),
            "tpr_observed": tpr, "fpr_observed": fpr, "precision_observed_test_mix": ratio(tp, tp+fp, assessed=tp+fp),
            "tpr_bounds": {"lower": tpr_low, "upper": tpr_high}, "fpr_bounds": {"lower": fpr_low, "upper": fpr_high},
            "routing_given_trigger": ratio(routing_correct, tp, assessed=routing_known),
            "end_to_end_routing_verified": ratio(end_correct, positive_total, assessed=positive_total-end_unknown),
            "end_to_end_routing_possible": ratio(end_correct+end_unknown, positive_total, assessed=positive_total-end_unknown),
            "ppv_scenarios": [{"assumed_base_rate": base, "value": ppv(base, tpr["value"], fpr["value"]),
                               "possible_lower": ppv(base, tpr_low["value"], fpr_high["value"]),
                               "possible_upper": ppv(base, tpr_high["value"], fpr_low["value"])} for base in base_rates],
            "assumption": "PPV requires transferable class-conditional rates; base rates are assumptions, not measured deployment prevalence."}


def summarize_costs(runs: list[dict[str, Any]], *, successes: int | None = None) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        groups[run["cost_scope"]].append(run)
    result = {}
    for scope, records in sorted(groups.items()):
        metrics = {}
        for field in ("input_total", "input_cached", "input_cache_write", "output_total", "output_reasoning", "model_calls", "estimated_cost_usd"):
            values = [record.get("usage", {}).get(field) for record in records]
            known = [value for value in values if value is not None]
            for value in known:
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    raise ValueError(f"Invalid usage measurement: {field}")
            metrics[field] = {"total": sum(known) if len(known) == len(values) else None,
                              "observed_sum": sum(known) if known else None, "known_records": len(known),
                              "records": len(records), "coverage": len(known)/len(records)}
        result[scope] = {"runs": len(records), "usage": metrics}
    production = [record for scope in ("production_writer", "downstream_executor") for record in groups.get(scope, [])]
    costs = [record.get("usage", {}).get("estimated_cost_usd") for record in production]
    known_cost = sum(costs) if costs and all(value is not None for value in costs) else None
    unit = ratio(known_cost, successes) if successes is not None else {"value": None, "numerator": known_cost, "denominator": None, "coverage": None, "status": "not_evaluated"}
    return {"by_cost_scope": result, "production_cost_per_success_usd": unit,
            "note": "All attempts are retained in actual spend; unknown usage is never filled with zero. Evaluation cost is separate."}


def compare_reviewers(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare AI to frozen human labels at aligned required-fact and artifact levels.

    Extracted claims are not aligned by list position and receive no agreement score.
    Artifact-level error-type detection allows different reasonable claim splits.
    """
    types = ("negation", "modality", "condition", "scope", "causality", "actor_object", "quantity_unit",
             "time_version", "citation", "unsupported_addition", "required_omission", "permission", "execution", "other")
    counters = {kind: Counter() for kind in types}
    facts = Counter()
    supplied_pairs = complete_pairs = 0
    for row in records:
        human, ai = row.get("human_review"), row.get("ai_review")
        if human is None or ai is None:
            continue
        if row.get("human_stage", "initial") != "initial":
            raise ValueError("Judge calibration must use frozen independent human initial labels")
        supplied_pairs += 1
        hm, am = semantic_metrics(human, row.get("task")), semantic_metrics(ai, row.get("task"))
        hn, an = as_semantic_review(human), as_semantic_review(ai)
        hf = {item["fact_id"]: item["status"] for item in hn["required_facts"]}
        af = {item["fact_id"]: item["status"] for item in an["required_facts"]}
        expected_ids = {item["id"] for item in row["task"]["required_facts"]} if row.get("task") else set(hf) | set(af)
        for fact_id in expected_ids:
            h, a = hf.get(fact_id), af.get(fact_id)
            if h not in {"preserved", "missing", "altered"} or a not in {"preserved", "missing", "altered"}:
                facts["unresolved"] += 1
            else:
                facts["determined"] += 1
                facts["exact_status_agreement"] += h == a
                h_error, a_error = h != "preserved", a != "preserved"
                facts[("tp" if a_error else "fn") if h_error else ("fp" if a_error else "tn")] += 1
        if not hm["review_complete"] or not am["review_complete"]:
            continue
        complete_pairs += 1
        for kind in types:
            h, a = kind in hm["error_types"], kind in am["error_types"]
            counters[kind][("tp" if a else "fn") if h else ("fp" if a else "tn")] += 1
    by_type = {}
    for kind, counts in counters.items():
        tp, fp, fn, tn = (counts[name] for name in ("tp", "fp", "fn", "tn"))
        by_type[kind] = {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
                         "sensitivity": ratio(tp, tp+fn, assessed=tp+fn), "false_positive_rate": ratio(fp, fp+tn, assessed=fp+tn),
                         "precision": ratio(tp, tp+fp, assessed=tp+fp)}
    return {"assigned_pairs": len(records), "supplied_pairs": supplied_pairs, "complete_pairs": complete_pairs,
            "pair_coverage": ratio(complete_pairs, len(records), assessed=len(records)),
            "by_error_type_artifact_presence": by_type, "aligned_required_facts": dict(facts),
            "required_fact_exact_status_agreement": ratio(facts["exact_status_agreement"], facts["determined"], assessed=facts["determined"]),
            "claim_agreement": None, "claim_agreement_reason": "Free claim extraction has not been aligned; no agreement percentage is computed.",
            "reference": "Frozen independent human initial judgments; adjudication is a separate analysis."}
