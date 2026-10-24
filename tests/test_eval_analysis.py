from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from eval.analysis import (
    compare_ai_reviews, compare_reviewers, ppv, ratio, scenario_macro, semantic_metrics,
    summarize_ai_reviews, summarize_costs, summarize_execution, summarize_reviews, summarize_triggers,
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


JUDGES = ["deepseek", "gpt", "gemini_argon", "gemini_flash", "claude_opus", "claude_sonnet"]


def ai_sidecar(judge, value=None, status="completed"):
    return {"judge_id": judge, "model": "synthetic/" + judge, "status": status, "review": value}


def ai_artifact(identifier, sidecars, *, scenario="scenario-one", facts=2):
    return {"artifact_id": identifier, "scenario_id": scenario,
            "task": {"required_facts": [{"id": f"r{i}", "text": "source fact"} for i in range(facts)]},
            "ai_reviews": sidecars}


def test_ai_only_retains_all_judges_and_failed_or_missing_denominators():
    rows = [ai_artifact("one", [ai_sidecar("deepseek", review(fact_statuses=("preserved", "missing"))),
                                ai_sidecar("gpt", status="timeout")]),
            ai_artifact("two", [ai_sidecar("deepseek", review(fact_statuses=("preserved", "preserved")))], scenario="scenario-two")]
    result = summarize_ai_reviews(rows, JUDGES)
    assert list(result["by_judge"]) == JUDGES
    assert result["human_reference"] is None and result["human_acceptance"] == "not_run"
    deepseek = result["by_judge"]["deepseek"]
    assert deepseek["assigned_artifacts"] == 2 and deepseek["reviews_supplied"] == 2
    assert deepseek["fixed_required_facts"]["assigned"] == 4
    assert deepseek["fixed_required_facts"]["statuses"]["missing"] == 1
    assert deepseek["macro"]["rfr"]["value"] == 0.75
    for judge in JUDGES[1:]:
        missing = result["by_judge"][judge]
        assert missing["assigned_artifacts"] == 2 and missing["reviews_supplied"] == 0
        assert missing["supplied_review_coverage"]["value"] == 0
        assert missing["macro"]["rfr"]["value"] is None
        assert missing["fixed_required_facts"]["statuses"]["no_review"] == 4
        assert missing["critical_prevalence"]["possible_upper"]["value"] == 1
    assert result["by_judge"]["gpt"]["review_statuses"] == {"not_recorded": 1, "timeout": 1}
    assert len(result["required_fact_comparison"]["pairs"]) == 15
    assert not {"accuracy", "calibration_passed", "majority_label"} & result.keys()


def test_ai_comparison_aligns_fixed_ids_and_excludes_unresolved_states_from_observed_rate():
    left = review(fact_statuses=("preserved", "altered"))
    right = review(("supported", "supported"), ("preserved", "altered"))
    right["required_facts"].reverse()
    rows = [ai_artifact("one", [ai_sidecar("left", left), ai_sidecar("right", right)]),
            ai_artifact("two", [ai_sidecar("left", review(fact_statuses=("missing", "unassessable"))),
                                ai_sidecar("right", review(fact_statuses=("altered", "preserved")))])]
    result = compare_ai_reviews(rows, ["left", "right"])
    pair = result["pairs"][0]
    assert pair["assigned_required_facts"] == 4 and pair["both_reviewed"] == 4
    assert pair["both_determined"] == 3 and pair["determined_disagreements"] == 1
    assert pair["observed_status_disagreement"]["value"] == 1/3
    assert pair["disagreement_bounds"]["lower"]["value"] == 0.25
    assert pair["disagreement_bounds"]["upper"]["value"] == 0.5
    assert sum(item["count"] for item in pair["status_matrix"]) == 4
    assert pair["facts"][1] == {"artifact_id": "one", "scenario_id": "scenario-one", "fact_id": "r1",
                                "left_status": "altered", "right_status": "altered"}
    assert result["claim_agreement"] is None


def test_ai_comparison_missing_reviews_and_omitted_facts_remain_unknown():
    rows = [ai_artifact("one", [ai_sidecar("left", review()), ai_sidecar("right", status="failed")])]
    result = summarize_ai_reviews(rows, ["left", "right"])
    assert result["by_judge"]["left"]["fixed_required_facts"]["statuses"]["unreviewed"] == 1
    assert result["by_judge"]["left"]["completed_review_coverage"]["value"] == 0
    pair = result["required_fact_comparison"]["pairs"][0]
    assert pair["assigned_required_facts"] == pair["unresolved_required_facts"] == 2
    assert pair["observed_status_disagreement"]["value"] is None
    assert pair["disagreement_bounds"]["lower"]["value"] == 0
    assert pair["disagreement_bounds"]["upper"]["value"] == 1


@pytest.mark.parametrize("bad_review", [None, {}, {**review(), "required_facts": [*review()["required_facts"], *review()["required_facts"]]}])
def test_ai_malformed_completed_sidecars_are_not_valid_reviews(bad_review):
    result = summarize_ai_reviews([ai_artifact("one", [ai_sidecar("left", bad_review)])], ["left"])
    judge = result["by_judge"]["left"]
    assert judge["review_statuses"] == {"invalid_review": 1}
    assert judge["reviews_supplied"] == 0 and judge["validation_errors"]
    assert judge["fixed_required_facts"]["statuses"]["no_review"] == 2


def test_ai_unknown_facts_and_ambiguous_identities_are_rejected():
    unknown = review()
    unknown["required_facts"][0]["fact_id"] = "unexpected"
    result = summarize_ai_reviews([ai_artifact("one", [ai_sidecar("left", unknown)])], ["left"])
    assert result["by_judge"]["left"]["review_statuses"] == {"invalid_review": 1}
    duplicate = ai_artifact("one", [ai_sidecar("left", review()), ai_sidecar("left", review())])
    with pytest.raises(ValueError, match="unique configured"):
        compare_ai_reviews([duplicate], ["left"])
    with pytest.raises(ValueError, match="distinct"):
        summarize_ai_reviews([ai_artifact("one", []), ai_artifact("one", [])], ["left"])
    with pytest.raises(ValueError, match="unique configured"):
        summarize_ai_reviews([ai_artifact("one", [ai_sidecar("unplanned", review())])], ["left"])


def test_ai_disagreement_macro_weights_scenarios_not_number_of_repeats():
    rows = [ai_artifact(str(i), [ai_sidecar("left", review()), ai_sidecar("right", review())], facts=1) for i in range(9)]
    rows.append(ai_artifact("last", [ai_sidecar("left", review()), ai_sidecar("right", review(fact_statuses=("missing",)))],
                            scenario="scenario-two", facts=1))
    pair = compare_ai_reviews(rows, ["left", "right"])["pairs"][0]
    assert pair["observed_status_disagreement"]["value"] == 0.1
    assert pair["scenario_macro"]["observed_disagreement"]["value"] == 0.5


def synthetic_task(identifier, scenario):
    return {"id": identifier, "scenario_id": scenario, "profile": "explanation", "language": "en",
            "prompt": "Explain the supplied source.", "sources": [{"id": "s1", "text": "quote"}],
            "required_facts": [{"id": "r0", "text": "first fact"}, {"id": "r1", "text": "second fact"}],
            "allowed_transformations": [], "output_contract": {},
            "rubric": {severity: [] for severity in ("critical", "major", "minor", "style_only")},
            "synthetic": True, "executable": False}


def synthetic_report_experiment(tmp_path, mode="ai_only"):
    from eval.common import digest, write_json
    from eval.review_store import ReviewStore

    path = tmp_path / mode
    inputs, jobs = path / "inputs", path / "jobs"
    (inputs / "tasks").mkdir(parents=True)
    (inputs / "calibration").mkdir()
    jobs.mkdir()
    tasks = [synthetic_task("task-one", "scenario-one"), synthetic_task("task-two", "scenario-two")]
    for task in tasks:
        write_json(inputs / "tasks" / (task["id"] + ".json"), task)
    calibration = {"review_id": "authored-one", "batch_id": "source-batch", "task": tasks[0], "candidate_text": "quote"}
    write_json(inputs / "calibration" / "one.json", calibration)
    judges = JUDGES if mode == "ai_only" else JUDGES[:2]
    plan = {"review_mode": mode, "judge_roles": judges, "max_calls": 276 if mode == "ai_only" else 128, "max_seconds": 14400}
    manifest = {"plan": plan, "lineage": {"source_experiment": "synthetic-source", "inherited_calls": 1}}
    write_json(path / "experiment.json", manifest)
    assignments = []
    for task in tasks:
        writer_id = "write-" + task["id"] + "-A"
        assignments.append({"assignment_id": writer_id, "task_id": task["id"], "scenario_id": task["scenario_id"],
                            "track": "product_native", "arm": "A", "phase": "writer", "role": "writer"})
        for judge in judges:
            review_id = "candidate-" + digest(writer_id)[:12]
            assignments.append({"assignment_id": "judge-" + review_id + "-" + judge,
                                "task_id": task["id"], "scenario_id": task["scenario_id"], "track": "product_native",
                                "arm": "blinded", "phase": "judge", "role": judge,
                                "review_id": review_id, "source_assignment": writer_id})
    for judge in judges:
        review_id = "cal-" + digest(calibration["review_id"])[:12]
        assignments.append({"assignment_id": "judge-" + review_id + "-" + judge, "task_id": tasks[0]["id"],
                            "scenario_id": tasks[0]["scenario_id"], "track": "calibration", "arm": "blinded",
                            "phase": "judge", "role": judge, "review_id": review_id})
    failed = next(row for row in assignments if row["phase"] == "writer" and row["task_id"] == tasks[1]["id"])
    failed = {**failed, "attempt_id": failed["assignment_id"] + "--01", "retry_of": None, "status": "failed",
              "cost_scope": "production_writer", "usage": {}, "outcomes": {}}
    (jobs / failed["attempt_id"]).mkdir()
    write_json(jobs / failed["attempt_id"] / "run.json", failed)
    exp = SimpleNamespace(path=path, inputs=inputs, jobs=jobs, name=mode, plan=plan, manifest=manifest,
                          judge_roles=judges, review_mode=mode, pilot_batch=mode + "-pilot", calibration_batch=mode + "-calibration",
                          assignments=lambda: assignments, records=lambda: [failed], store=ReviewStore(path / "reviews.sqlite"),
                          budget=SimpleNamespace(snapshot=lambda: {"calls": 1, "seconds": 2.5, "pending": 0,
                                                                   "max_calls": plan["max_calls"], "max_seconds": plan["max_seconds"]}))
    writer_id = "write-" + tasks[0]["id"] + "-A"
    packet = {"review_id": "candidate-" + digest(writer_id)[:12], "batch_id": exp.pilot_batch,
              "artifact_hash": digest("quote"), "candidate_text": "quote", "task": tasks[0],
              "private": {"track": "product_native", "arm": "A", "writer_attempt": writer_id + "--01"},
              "ai_reviews": [ai_sidecar("deepseek", review(fact_statuses=("preserved", "missing"))),
                             ai_sidecar("gpt", status="timeout")]}
    return exp, packet


def test_ai_report_is_immediate_and_retains_absent_batch_and_generation_failures(tmp_path):
    from eval.reporting import summarize

    exp, packet = synthetic_report_experiment(tmp_path)
    exp.store.import_batch(exp.pilot_batch, [packet], review_mode="ai_only")
    result = summarize(exp)
    report = json.loads((exp.path / "summary.json").read_text(encoding="utf-8"))
    assert result["human_batches"] == [] and result["review_mode"] == "ai_only"
    assert report["judge_roles"] == JUDGES and report["plan"] == exp.plan
    assert report["provenance"]["lineage"] == exp.manifest["lineage"]
    pilot = report["semantic"][exp.pilot_batch]["product_native/A"]
    assert pilot["artifacts_available"] == 1 and pilot["assigned_artifacts"] == 2
    assert len(pilot["unavailable_artifact_ids"]) == 1
    assert pilot["by_judge"]["deepseek"]["reviews_supplied"] == 1
    assert pilot["by_judge"]["deepseek"]["supplied_review_coverage"]["value"] == 0.5
    assert pilot["by_judge"]["deepseek"]["fixed_required_facts"]["assigned"] == 4
    assert pilot["by_judge"]["gpt"]["review_statuses"] == {"not_run": 1, "timeout": 1}
    assert pilot["by_judge"]["claude_sonnet"]["review_statuses"] == {"not_run": 2}
    calibration = report["semantic"][exp.calibration_batch]["calibration/calibration"]
    assert calibration["assigned_artifacts"] == 1 and calibration["artifacts_available"] == 0
    assert calibration["by_judge"]["deepseek"]["reviews_supplied"] == 0
    assert report["judge_calibration"][exp.pilot_batch]["status"] == "not_applicable"
    assert result["statuses"]["failed"] == 1
    markdown = (exp.path / "SUMMARY.md").read_text(encoding="utf-8")
    assert "1 / 276" in markdown and " / 128" not in markdown
    assert "gemini_argon" in markdown and "claude_sonnet" in markdown
    assert "Human review progress" not in markdown and "until the whole initial batch" not in markdown
    with exp.store._connection() as db:
        assert db.execute("SELECT COUNT(*) FROM human_reviews").fetchone()[0] == 0


def test_historical_report_keeps_open_batch_hidden_without_export(tmp_path, monkeypatch):
    from eval.reporting import summarize

    exp, packet = synthetic_report_experiment(tmp_path, mode="human_blind")
    exp.store.import_batch(exp.pilot_batch, [packet])
    def forbidden_export(*args, **kwargs):
        raise AssertionError("An open historical batch must not export semantic labels")
    monkeypatch.setattr(exp.store, "export_batch", forbidden_export)
    summarize(exp)
    report = json.loads((exp.path / "summary.json").read_text(encoding="utf-8"))
    assert report["semantic"][exp.pilot_batch]["status"] == "withheld_until_initial_freeze"
    assert report["judge_calibration"] == {}
    assert len(report["human_batches"]) == 1


def test_ai_report_rejects_human_blind_batch_instead_of_bypassing_freeze(tmp_path):
    from eval.reporting import summarize

    exp, packet = synthetic_report_experiment(tmp_path)
    exp.store.import_batch(exp.pilot_batch, [packet], review_mode="human_blind")
    with pytest.raises(ValueError, match="cannot reveal"):
        summarize(exp)


def test_historical_frozen_report_retains_human_and_ai_stages(tmp_path):
    from eval.reporting import summarize

    exp, packet = synthetic_report_experiment(tmp_path, mode="human_blind")
    batch = {"batch_id": exp.pilot_batch, "review_mode": "human_blind", "state": "frozen", "total": 1,
             "initial_submitted": 1, "adjudication_submitted": 0}
    frozen_packet = {**packet, "initial": {"state": "frozen", "review": review(fact_statuses=("preserved", "missing"))},
                     "adjudication": {"state": "empty"}}
    exp.store = SimpleNamespace(list_batches=lambda: [batch], export_batch=lambda *args, **kwargs: {"packets": [frozen_packet]})
    summarize(exp)
    report = json.loads((exp.path / "summary.json").read_text(encoding="utf-8"))
    stages = report["semantic"][exp.pilot_batch]
    assert stages["product_native/A/human_initial"]["assigned_artifacts"] == 2
    assert stages["product_native/A/human_initial"]["reviews_supplied"] == 1
    assert stages["product_native/A/human_adjudication"]["reviews_supplied"] == 0
    assert stages["product_native/A/ai_gpt"]["reviews_supplied"] == 0
    assert report["judge_calibration"][exp.pilot_batch]["deepseek"]["supplied_pairs"] == 1


def test_ai_report_full_frozen_inventory_without_any_model_calls(tmp_path, monkeypatch):
    import eval.runner as runner
    from eval.reporting import summarize

    monkeypatch.setattr(runner, "experiment_path", lambda name: tmp_path / name)
    exp = runner.Experiment("offline-ai-report", create=True, review_mode="ai_only")
    result = summarize(exp)
    report = json.loads((exp.path / "summary.json").read_text(encoding="utf-8"))
    assert result["budget"]["calls"] == 0
    assert report["assigned"] == len(exp.assignments())
    planned_reviews = sum(row["phase"] == "judge" for row in exp.assignments())
    summarized_reviews = sum(judge["assigned_artifacts"] for groups in report["semantic"].values()
                             for group in groups.values() for judge in group["by_judge"].values())
    assert planned_reviews == summarized_reviews
    assert all(judge["reviews_supplied"] == 0 for groups in report["semantic"].values()
               for group in groups.values() for judge in group["by_judge"].values())


def persisted_judge_attempt(exp, packet, *, number=1, status="completed", value=None):
    from eval.common import digest, write_json

    assigned = next(row for row in exp.assignments() if row.get("review_id") == packet["review_id"] and row["role"] == "deepseek")
    attempt_id = assigned["assignment_id"] + f"--{number:02d}"
    job = exp.jobs / attempt_id
    job.mkdir()
    sidecar = {"judge_id": "deepseek", "model": "synthetic/deepseek", "attempt_id": attempt_id,
               "status": status, "review": value}
    path = job / "semantic-review.json"
    write_json(path, sidecar)
    record = {**assigned, "attempt_id": attempt_id,
              "retry_of": assigned["assignment_id"] + f"--{number-1:02d}" if number > 1 else None,
              "status": status, "model": sidecar["model"], "cost_scope": "evaluation_only", "usage": {}, "outcomes": {},
              "review_refs": [{"review_id": packet["review_id"], "reviewer_id": "deepseek", "path": str(path),
                               "sha256": digest(path.read_bytes())}]}
    write_json(job / "run.json", record)
    records = [*exp.records(), record]
    exp.records = lambda: records
    return record, sidecar, path


def reported_judge(exp, *, batch_id=None, group="product_native/A"):
    from eval.reporting import summarize

    summarize(exp)
    report = json.loads((exp.path / "summary.json").read_text(encoding="utf-8"))
    return report["semantic"][batch_id or exp.pilot_batch][group]["by_judge"]["deepseek"]


def test_report_uses_saved_review_after_execution_before_database_update(tmp_path):
    exp, packet = synthetic_report_experiment(tmp_path)
    packet["ai_reviews"] = [ai_sidecar("deepseek", status="not_run")]
    exp.store.import_batch(exp.pilot_batch, [packet], review_mode="ai_only")
    record, sidecar, path = persisted_judge_attempt(exp, packet, value=review(fact_statuses=("preserved", "missing")))
    before = path.read_bytes()

    result = reported_judge(exp)
    assert result["assigned_artifacts"] == 2 and result["reviews_supplied"] == 1
    assert result["review_statuses"] == {"completed": 1, "not_run": 1}
    assert result["macro"]["rfr"]["value"] == 0.5
    artifact = next(row for row in result["artifacts"] if row["artifact_id"] == packet["review_id"])
    evidence = artifact["review_evidence"]
    assert evidence["source"] == "job_sidecar" and evidence["sidecar_verified"] is True
    assert evidence["attempt_id"] == record["attempt_id"]
    assert evidence["sidecar_sha256"] == evidence["reference_sha256"]
    assert path.read_bytes() == before
    stored = exp.store.export_batch(exp.pilot_batch, include_private=True)["packets"][0]
    assert stored["ai_reviews"][0]["status"] == "not_run"


def test_report_prefers_latest_retry_over_old_database_attempt(tmp_path):
    exp, packet = synthetic_report_experiment(tmp_path)
    first, old_sidecar, _ = persisted_judge_attempt(exp, packet, status="failed")
    packet["ai_reviews"] = [old_sidecar]
    exp.store.import_batch(exp.pilot_batch, [packet], review_mode="ai_only")
    latest, _, _ = persisted_judge_attempt(exp, packet, number=2, value=review(fact_statuses=("preserved", "preserved")))
    result = reported_judge(exp)
    artifact = next(row for row in result["artifacts"] if row["artifact_id"] == packet["review_id"])
    assert result["reviews_supplied"] == 1 and artifact["review_status"] == "completed"
    assert artifact["review_evidence"]["attempt_id"] == latest["attempt_id"]
    assert latest["retry_of"] == first["attempt_id"]
    stored = exp.store.export_batch(exp.pilot_batch, include_private=True)["packets"][0]
    assert stored["ai_reviews"][0]["attempt_id"] == first["attempt_id"]


@pytest.mark.parametrize("problem", ["missing_file", "hash_mismatch", "invalid_review", "wrong_identity", "missing_reference"])
def test_unverified_latest_review_cannot_fall_back_to_database_opinion(tmp_path, problem):
    from eval.common import digest, write_json

    exp, packet = synthetic_report_experiment(tmp_path)
    exp.store.import_batch(exp.pilot_batch, [packet], review_mode="ai_only")
    record, sidecar, path = persisted_judge_attempt(exp, packet, value=review(fact_statuses=("preserved", "preserved")))
    if problem == "missing_file":
        path.unlink()
    elif problem == "hash_mismatch":
        sidecar["review"] = review(fact_statuses=("preserved", "missing"))
        write_json(path, sidecar)
    elif problem in {"invalid_review", "wrong_identity"}:
        if problem == "invalid_review":
            sidecar["review"] = {}
        else:
            sidecar["judge_id"] = "gpt"
        write_json(path, sidecar)
        record["review_refs"][0]["sha256"] = digest(path.read_bytes())
    else:
        record["review_refs"] = []
    write_json(exp.jobs / record["attempt_id"] / "run.json", record)
    result = reported_judge(exp)
    assert result["reviews_supplied"] == 0
    assert result["review_statuses"] == {"not_run": 1, "review_unavailable": 1}
    artifact = next(row for row in result["artifacts"] if row["artifact_id"] == packet["review_id"])
    assert artifact["review_evidence"]["source"] == "run_record"
    assert artifact["review_evidence"]["sidecar_verified"] is False
    assert artifact["review_evidence"]["reason"]
    assert result["fixed_required_facts"]["statuses"]["no_review"] == 4


def test_latest_failed_attempt_is_reported_even_when_database_says_not_run(tmp_path):
    exp, packet = synthetic_report_experiment(tmp_path)
    packet["ai_reviews"] = [ai_sidecar("deepseek", status="not_run")]
    exp.store.import_batch(exp.pilot_batch, [packet], review_mode="ai_only")
    record, _, path = persisted_judge_attempt(exp, packet, status="timeout")
    path.unlink()
    result = reported_judge(exp)
    assert result["review_statuses"] == {"not_run": 1, "timeout": 1}
    assert result["reviews_supplied"] == 0
    artifact = next(row for row in result["artifacts"] if row["artifact_id"] == packet["review_id"])
    assert artifact["review_evidence"]["attempt_id"] == record["attempt_id"]
    assert artifact["review_evidence"]["source"] == "run_record"


def test_report_does_not_infer_a_candidate_when_only_a_judge_sidecar_exists(tmp_path, monkeypatch):
    import eval.reporting as reporting

    exp, packet = synthetic_report_experiment(tmp_path)
    persisted_judge_attempt(exp, packet, value=review(fact_statuses=("preserved", "preserved")))
    def forbidden_review_validation(*args, **kwargs):
        raise AssertionError("A missing packet cannot supply frozen candidate evidence")
    monkeypatch.setattr(reporting, "validate_review", forbidden_review_validation)
    result = reported_judge(exp)
    assert result["reviews_supplied"] == 0 and result["assigned_artifacts"] == 2
    artifact = next(row for row in result["artifacts"] if row["artifact_id"] == packet["review_id"])
    assert artifact["review_status"] == "review_unavailable"
    assert artifact["review_evidence"]["reason"] == "artifact_packet_unavailable"


def review_with_edit():
    value = review(fact_statuses=("preserved", "preserved"))
    value["edits"] = [{"id": "e1", "original_span": "quote", "candidate_span": "quote",
                       "semantic_category": "other", "severity": "style_only",
                       "source_evidence": [{"source_id": "s1", "span": "quote"}],
                       "justification": "A synthetic edit annotation with source evidence."}]
    return value


@pytest.mark.parametrize("persisted", [True, False])
def test_report_preserves_missing_original_semantics_for_edits_after_store_export(tmp_path, persisted):
    from eval.contracts import validate_review

    exp, packet = synthetic_report_experiment(tmp_path)
    value = validate_review(review_with_edit(), packet["task"], packet["candidate_text"], packet.get("original_text"))
    # This is the real storage boundary that used to turn a valid review into
    # invalid_review: missing/None becomes an explicit empty string on export.
    packet["ai_reviews"] = [ai_sidecar("deepseek", value)]
    exp.store.import_batch(exp.pilot_batch, [packet], review_mode="ai_only")
    stored_before = exp.store.export_batch(exp.pilot_batch, include_private=True)["packets"][0]
    assert stored_before["original_text"] == ""
    with pytest.raises(ValueError, match="original_span"):
        validate_review(value, packet["task"], packet["candidate_text"], stored_before["original_text"])
    if persisted:
        record, _, path = persisted_judge_attempt(exp, packet, value=value)
        run_path = exp.jobs / record["attempt_id"] / "run.json"
        unchanged_files = {path: path.read_bytes(), run_path: run_path.read_bytes()}
    else:
        unchanged_files = {}

    result = reported_judge(exp)
    artifact = next(row for row in result["artifacts"] if row["artifact_id"] == packet["review_id"])
    assert result["reviews_supplied"] == 1
    assert result["review_statuses"] == {"completed": 1, "not_run": 1}
    assert artifact["review_evidence"]["source"] == ("job_sidecar" if persisted else "review_store")
    assert artifact["review_evidence"]["sidecar_verified"] is persisted
    assert result["validation_errors"] == []
    stored_after = exp.store.export_batch(exp.pilot_batch, include_private=True)["packets"][0]
    assert stored_after == stored_before
    assert all(path.read_bytes() == original for path, original in unchanged_files.items())


@pytest.mark.parametrize("original,valid", [(None, True), ("", False), ("quote", True), ("different original", False)])
def test_calibration_original_is_recovered_from_frozen_input_without_weakening_empty_text(tmp_path, original, valid):
    from eval.common import digest, read_json, write_json
    from eval.contracts import load_calibration_packets, validate_review

    exp, _ = synthetic_report_experiment(tmp_path)
    source_path = exp.inputs / "calibration" / "one.json"
    source = read_json(source_path)
    if original is not None:
        source["original_text"] = original
        write_json(source_path, source)
    packet = load_calibration_packets(exp.inputs / "calibration")[0]
    packet.update(review_id="cal-" + digest(packet["review_id"])[:12], batch_id=exp.calibration_batch,
                  private={"arm": "calibration"}, ai_reviews=[ai_sidecar("deepseek", status="not_run")])
    value = review_with_edit()
    if valid:
        value = validate_review(value, packet["task"], packet["candidate_text"], packet.get("original_text"))
    else:
        with pytest.raises(ValueError, match="original_span"):
            validate_review(value, packet["task"], packet["candidate_text"], packet.get("original_text"))
    exp.store.import_batch(exp.calibration_batch, [packet], review_mode="ai_only")
    _, _, sidecar_path = persisted_judge_attempt(exp, packet, value=value)
    before = sidecar_path.read_bytes()
    result = reported_judge(exp, batch_id=exp.calibration_batch, group="calibration/calibration")
    assert result["assigned_artifacts"] == 1 and result["reviews_supplied"] == int(valid)
    assert result["review_statuses"] == ({"completed": 1} if valid else {"review_unavailable": 1})
    assert sidecar_path.read_bytes() == before
    assert read_json(source_path) == source
