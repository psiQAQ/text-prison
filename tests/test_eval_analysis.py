from copy import deepcopy

import pytest

from eval.analysis import (
    compare_reviewers, ppv, ratio, scenario_macro, semantic_metrics,
    summarize_costs, summarize_execution, summarize_reviews, summarize_triggers,
)


def review(claim_statuses=("supported",), fact_statuses=("preserved",)):
    result = {"review_version": "0.2", "source_coverage": {"status": "adequate", "affected_source_ids": [], "note": ""},
              "claims": [], "required_facts": [], "edits": [], "uncertain_items": []}
    for name, statuses in (("claims", claim_statuses), ("required_facts", fact_statuses)):
        for index, status in enumerate(statuses):
            bad = status in {"contradicted", "unsupported", "missing", "altered"}
            item = {"status": status, "candidate_span": None if status == "missing" else "quote",
                    "source_evidence": [{"source_id": "s1", "span": None}], "justification": "evidence",
                    "severity": "major" if bad else None, "error_types": ["quantity_unit"] if bad else []}
            if name == "claims":
                item.update(id=f"c{index}", text="claim")
            else:
                item["fact_id"] = f"r{index}"
            result[name].append(item)
    return result


def executor(assignment, scenario, success, status="completed", retry_of=None):
    return {"phase": "executor", "assignment_id": assignment, "scenario_id": scenario,
            "attempt_id": assignment + ("-retry" if retry_of else "-first"), "retry_of": retry_of,
            "status": status, "outcomes": {"agent_success": success}}


def test_support_and_required_retention_are_not_conflated():
    metrics = semantic_metrics(review(("supported", "supported"), ("preserved", "missing")))
    assert metrics["fsp_verified"]["value"] == 1
    assert metrics["rfr"]["value"] == 0.5
    assert metrics["status"] == "failed"


def test_possible_ranges_and_determined_coverage_include_unknowns():
    metrics = semantic_metrics(review(("supported", "contradicted", "unassessable", "unsupported"), ("preserved", "unassessable")))
    assert metrics["fsp_verified"]["value"] == 0.25
    assert metrics["fsp_possible"]["value"] == 0.5
    assert metrics["claim_determined_coverage"]["value"] == 0.75
    assert metrics["rfr"]["value"] == 0.5
    assert metrics["rfr_possible"]["value"] == 1
    assert metrics["critical_present"] is None


def test_zero_denominators_and_missing_review_never_get_full_scores():
    metrics = semantic_metrics(review((), ()))
    assert metrics["fsp_verified"]["value"] is None
    assert metrics["rfr"]["status"] == "undefined"
    assert metrics["status"] == "not_evaluated"
    assert semantic_metrics(None)["fsp_verified"] is None
    assert ratio(0, 0)["value"] is None


def test_scenario_macro_does_not_reward_many_repeats():
    rows = [{"scenario_id": "many", "score": 1} for _ in range(9)]
    rows += [{"scenario_id": "one", "score": 0}, {"scenario_id": "unknown", "score": None}]
    value = scenario_macro(rows, "score")
    assert value["value"] == 0.5
    assert value["scenario_denominator"] == 3
    assert value["coverage"] == 2/3


def test_critical_prevalence_reports_all_assigned_artifacts_and_uncertainty():
    critical = review(("contradicted",))
    critical["claims"][0]["severity"] = "critical"
    result = summarize_reviews([{"scenario_id": "s1", "review": critical},
                                {"scenario_id": "s2", "review": review()},
                                {"scenario_id": "s3", "review": None}])
    assert result["critical_prevalence"]["verified_lower"]["value"] == 1/3
    assert result["critical_prevalence"]["possible_upper"]["value"] == 2/3
    assert result["completed_review_coverage"]["value"] == 2/3


def test_mixed_reviewers_or_arms_are_not_silently_pooled():
    with pytest.raises(ValueError, match="reviewer_id"):
        summarize_reviews([{"scenario_id": "s1", "review": review(), "reviewer_id": "human"},
                           {"scenario_id": "s1", "review": review(), "reviewer_id": "ai"}])


def test_first_attempt_failure_is_not_replaced_by_successful_retry():
    runs = [executor("a", "s1", None, status="timeout"), executor("a", "s1", True, retry_of="a-first"),
            executor("b", "s2", True), executor("c", "s3", None, status="not_run")]
    result = summarize_execution(runs)
    assert result["assigned"] == 3
    assert result["attempts_including_retries"] == 4
    assert result["first_complete_success_verified"]["value"] == 1/3
    assert result["first_complete_success_possible"]["value"] == 2/3
    assert result["unknown"] == 1


def test_missing_original_retry_record_fails_instead_of_selecting_best():
    with pytest.raises(ValueError, match="exactly one original"):
        summarize_execution([executor("a", "s1", True, retry_of="lost")])


def test_non_boolean_success_is_rejected():
    with pytest.raises(ValueError, match="boolean"):
        summarize_execution([executor("a", "s1", 1)])


def test_trigger_unknowns_are_not_counted_as_negative_and_routes_use_exact_set():
    rows = [
        {"expected_trigger": True, "trigger_observed": True, "expected_profiles": ["procedure"], "observed_profiles": ["procedure", "reference"], "expected_language": "en", "observed_language": "en"},
        {"expected_trigger": True, "trigger_observed": None},
        {"expected_trigger": False, "trigger_observed": False},
        {"expected_trigger": False, "trigger_observed": None},
    ]
    result = summarize_triggers(rows)
    assert result["counts"]["fn"] == 0
    assert result["tpr_bounds"]["lower"]["value"] == 0.5
    assert result["tpr_bounds"]["upper"]["value"] == 1
    assert result["fpr_bounds"]["upper"]["value"] == 0.5
    assert result["observation_coverage"]["value"] == 0.5
    assert result["routing_given_trigger"]["value"] == 0


def test_ppv_uses_explicit_base_rate_and_keeps_undefined_cases():
    assert ppv(0.05, 0.9, 0.05) == pytest.approx(0.4864864865)
    assert ppv(0.5, 0.9, 0.05) == pytest.approx(0.9473684211)
    assert ppv(0.5, 0, 0) is None
    assert ppv(0.5, None, 0.05) is None
    with pytest.raises(ValueError):
        ppv(1.1, 0.9, 0.05)


def test_costs_split_books_keep_missing_and_zero_success_undefined():
    runs = [
        {"cost_scope": "production_writer", "usage": {"input_total": 10, "output_total": 2, "estimated_cost_usd": 0.1}},
        {"cost_scope": "production_writer", "usage": {"input_total": None, "output_total": 3, "estimated_cost_usd": None}},
        {"cost_scope": "evaluation_only", "usage": {"input_total": 50, "output_total": 20, "estimated_cost_usd": 7}},
    ]
    result = summarize_costs(runs, successes=0)
    writer = result["by_cost_scope"]["production_writer"]["usage"]
    assert writer["input_total"]["total"] is None
    assert writer["input_total"]["observed_sum"] == 10
    assert writer["input_total"]["coverage"] == 0.5
    assert result["production_cost_per_success_usd"]["value"] is None
    assert result["production_cost_per_success_usd"]["status"] == "undefined"


def test_independent_human_schema_is_converted_without_mutation():
    human = {"review_version": "0.2", "source_coverage": "adequate", "coverage_note": "",
             "claims": [{"id": "h1", "text": "claim", "status": "unsupported", "candidate_span": "claim",
                         "severity": "major", "source_refs": [], "justification": "No source."}],
             "required_facts": [], "uncertain_items": [], "no_claims_confirmed": False,
             "adjudication_reason": ""}
    before = deepcopy(human)
    metrics = semantic_metrics(human)
    assert human == before
    assert metrics["status"] == "failed"
    assert metrics["error_types"] == ["other"]


def test_calibration_compares_aligned_required_facts_not_arbitrary_claim_indices():
    human = review(("contradicted",), ("altered",))
    ai = review(("supported", "supported"), ("preserved",))
    result = compare_reviewers([{"human_review": human, "ai_review": ai}])
    assert result["by_error_type_artifact_presence"]["quantity_unit"]["fn"] == 1
    assert result["aligned_required_facts"]["fn"] == 1
    assert result["claim_agreement"] is None
    assert result["required_fact_exact_status_agreement"]["value"] == 0
    with pytest.raises(ValueError, match="independent"):
        compare_reviewers([{"human_review": human, "ai_review": ai, "human_stage": "adjudication"}])
