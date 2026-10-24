"""Synthetic review fixtures: these do not constitute human or model results."""

from copy import deepcopy
import hashlib
import http.client
import json
from pathlib import Path
import socket
import sqlite3
import threading
import time

import pytest

from eval.review_store import ConflictError, ReviewError, ReviewStore, blank_review
from eval.web import MAX_BODY_BYTES, build_server


def packet(review_id="hidden-arm-A", candidate="The synthetic timeout is 30 s."):
    return {
        "review_id": review_id, "batch_id": "synthetic-test",
        "artifact_hash": hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
        "candidate_text": candidate,
        "task": {
            "id": "private-task-identity", "scenario_id": "private-scenario-identity",
            "profile": "explanation", "language": "en", "prompt": "Explain the synthetic timeout.",
            "sources": [{"id": "S1", "text": "The synthetic timeout is 30 s."}],
            "required_facts": [{"id": "F1", "text": "Timeout equals 30 s."}],
            "allowed_transformations": ["Use an equivalent duration unit."],
        },
        "private": {"arm": "private-arm-A", "writer_model": "private-model"},
        "ai_reviews": [{"judge_id": "hidden-ai-judge", "review": {"claims": [{"text": "hidden-ai-claim"}]}}],
    }


def completed_review(source_packet):
    review = blank_review(source_packet["task"])
    review["source_coverage"] = "adequate"
    review["claims"] = [{
        "id": "human-claim-1", "text": source_packet["candidate_text"],
        "candidate_span": source_packet["candidate_text"], "status": "supported",
        "severity": None, "source_refs": [{"source_id": "S1", "evidence": "30 s"}],
        "justification": "The synthetic source gives the same timeout.",
    }]
    review["required_facts"] = [{
        "id": "F1", "status": "preserved", "candidate_span": "30 s",
        "severity": None, "source_refs": [{"source_id": "S1", "evidence": "30 s"}],
        "justification": "The required duration is present.",
    }]
    return review


@pytest.fixture
def store(tmp_path):
    return ReviewStore(tmp_path / "review.sqlite3")


def save(store, source_packet, review=None, *, stage="initial", revision=0, submit=True, request_id=None):
    return store.save_review(source_packet["review_id"], completed_review(source_packet) if review is None else review,
                             artifact_hash=source_packet["artifact_hash"], expected_revision=revision,
                             stage=stage, submit=submit, request_id=request_id)


def test_blind_views_exclude_ai_and_assignment_server_side(store):
    source = packet()
    listing = store.import_batch("synthetic-test", [source])
    public_id = listing["packets"][0]["review_id"]
    assert public_id != source["review_id"]
    view = store.get_packet(public_id)
    assert view["initial"]["review"]["claims"] == []
    assert view["initial"]["review"]["required_facts"][0]["status"] == ""
    exports = json.dumps(store.export_batch("synthetic-test"))
    for secret in ("hidden-arm-A", "private-arm-A", "private-model", "hidden-ai-judge", "hidden-ai-claim", "private-task-identity", "private-scenario-identity"):
        assert secret not in exports
    assert "ai_reviews" not in view and "adjudication" not in view
    assert view["review_mode"] == listing["batch"]["review_mode"] == "human_blind"


def test_ai_only_reveals_multiple_models_without_human_records(store):
    source = packet()
    source["ai_reviews"] = [
        {"judge_id": "synthetic-codex", "status": "completed", "review": {"claims": [{"text": "Synthetic first evidence."}]}},
        {"judge_id": "synthetic-deepseek", "status": "completed", "review": {"claims": [{"text": "Synthetic second evidence."}]}},
        {"judge_id": "synthetic-gemini", "status": "invalid_review", "review": None, "error": "Synthetic malformed response."},
        {"judge_id": "synthetic-claude", "status": "pending", "review": None},
    ]
    listing = store.import_batch("synthetic-test", [source], review_mode="ai_only")
    view = store.get_packet(listing["packets"][0]["review_id"])
    progress = {"recorded": 4, "completed": 2, "statuses": {"completed": 2, "invalid_review": 1, "pending": 1}}
    assert listing["batch"]["state"] == "open"
    assert listing["batch"]["frozen_at"] is None
    assert view["review_mode"] == listing["batch"]["review_mode"] == "ai_only"
    assert view["ai_revealed"] and view["ai_reviews"] == source["ai_reviews"]
    assert view["ai_progress"] == listing["packets"][0]["ai_progress"] == progress
    assert store.list_batches()[0]["ai_progress"] == progress
    assert "initial_submitted" not in store.list_batches()[0]
    for item in (view, listing["packets"][0]):
        assert "initial" not in item and "adjudication" not in item
    for stage in ("initial", "adjudication"):
        with pytest.raises(ConflictError, match="AI-only"):
            save(store, source, stage=stage, request_id=f"synthetic-{stage}")
    with pytest.raises(ConflictError, match="AI-only"):
        store.freeze_batch("synthetic-test")
    assert store.history(source["review_id"]) == []
    with sqlite3.connect(store.db_path) as db:
        for table in ("human_reviews", "review_history", "requests"):
            assert db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    exported = store.export_batch("synthetic-test")
    assert exported["batch"]["review_mode"] == "ai_only"
    assert exported["packets"][0]["ai_reviews"] == source["ai_reviews"]
    assert exported["packets"][0]["history"] == []
    assert "initial" not in exported["packets"][0] and "adjudication" not in exported["packets"][0]
    assert "没有人工初判或裁决" in exported["interpretation"]
    assert "private-model" not in json.dumps(exported)


def test_ai_only_progress_updates_and_empty_evidence_are_not_success(store):
    source = packet()
    source["ai_reviews"] = []
    store.import_batch("synthetic-test", [source], review_mode="ai_only")
    assert store.get_packet(source["review_id"])["ai_progress"] == {"recorded": 0, "completed": 0, "statuses": {}}
    source["ai_reviews"] = [{"judge_id": "synthetic-judge", "status": "pending", "review": None}]
    store.import_batch("synthetic-test", [source], review_mode="ai_only")
    assert store.get_packet(source["review_id"])["ai_progress"]["completed"] == 0
    source["ai_reviews"][0].update(status="completed", review={"claims": []})
    store.import_batch("synthetic-test", [source], review_mode="ai_only")
    assert store.get_packet(source["review_id"])["ai_progress"]["completed"] == 1
    assert store.history(source["review_id"]) == []


@pytest.mark.parametrize("initial_mode,new_mode", [("human_blind", "ai_only"), ("ai_only", "human_blind")])
def test_existing_batch_mode_cannot_change(store, initial_mode, new_mode):
    source = packet()
    store.import_batch("synthetic-test", [source], review_mode=initial_mode)
    before = store.export_batch("synthetic-test")
    with pytest.raises(ConflictError, match="模式不能改变"):
        store.import_batch("synthetic-test", [source], review_mode=new_mode)
    after = store.export_batch("synthetic-test")
    assert after["batch"] == before["batch"] and after["packets"] == before["packets"]


def test_import_rejects_unknown_review_mode(store):
    with pytest.raises(ReviewError, match="review_mode"):
        store.import_batch("synthetic-test", [packet()], review_mode="unknown")
    assert store.list_batches() == []


def test_legacy_database_migration_preserves_human_batch_and_records(tmp_path):
    path = tmp_path / "synthetic-legacy.sqlite3"
    source = packet()
    source["original_text"] = ""
    review = completed_review(source)
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE batches (batch_id TEXT PRIMARY KEY, state TEXT NOT NULL DEFAULT 'open',
                                  created_at TEXT NOT NULL, frozen_at TEXT);
            CREATE TABLE packets (review_id TEXT PRIMARY KEY, public_id TEXT UNIQUE NOT NULL,
                                  batch_id TEXT NOT NULL REFERENCES batches(batch_id),
                                  artifact_hash TEXT NOT NULL, packet_json TEXT NOT NULL, ordinal INTEGER NOT NULL);
            CREATE TABLE human_reviews (review_id TEXT NOT NULL REFERENCES packets(review_id), stage TEXT NOT NULL,
                                        revision INTEGER NOT NULL, state TEXT NOT NULL, payload_json TEXT NOT NULL,
                                        updated_at TEXT NOT NULL, PRIMARY KEY (review_id, stage));
            CREATE TABLE review_history (history_id INTEGER PRIMARY KEY AUTOINCREMENT, review_id TEXT NOT NULL,
                                         stage TEXT NOT NULL, revision INTEGER NOT NULL, action TEXT NOT NULL,
                                         payload_json TEXT NOT NULL, created_at TEXT NOT NULL);
        """)
        db.execute("INSERT INTO batches VALUES (?, 'frozen', ?, ?)", ("synthetic-test", "synthetic-created", "synthetic-frozen"))
        db.execute("INSERT INTO packets VALUES (?, 'legacy-public', ?, ?, ?, 1)",
                   (source["review_id"], "synthetic-test", source["artifact_hash"], json.dumps(source)))
        db.execute("INSERT INTO human_reviews VALUES (?, 'initial', 7, 'frozen', ?, 'synthetic-frozen')",
                   (source["review_id"], json.dumps(review)))
        db.execute("INSERT INTO review_history(review_id,stage,revision,action,payload_json,created_at) VALUES (?, 'initial', 7, 'freeze', ?, 'synthetic-frozen')",
                   (source["review_id"], json.dumps(review)))
    migrated = ReviewStore(path)
    exported = migrated.export_batch("synthetic-test")
    assert exported["batch"] == {"batch_id": "synthetic-test", "state": "frozen", "created_at": "synthetic-created",
                                 "frozen_at": "synthetic-frozen", "review_mode": "human_blind"}
    assert exported["packets"][0]["review_id"] == "legacy-public"
    assert exported["packets"][0]["initial"]["review"] == review
    assert exported["packets"][0]["initial"]["revision"] == 7
    assert exported["packets"][0]["history"][0]["review"] == review
    assert ReviewStore(path).get_packet("legacy-public")["initial"]["review"] == review


def test_freeze_requires_every_initial_then_preserves_independence(store):
    first, second = packet(), packet("hidden-arm-D")
    store.import_batch("synthetic-test", [first, second])
    save(store, first)
    with pytest.raises(ConflictError, match="每一份"):
        store.freeze_batch("synthetic-test")
    assert "ai_reviews" not in store.get_packet(first["review_id"])
    with pytest.raises(ConflictError, match="冻结后"):
        save(store, first, stage="adjudication")
    save(store, second)
    store.freeze_batch("synthetic-test")
    frozen = store.get_packet(first["review_id"])
    assert frozen["initial"]["state"] == "frozen"
    assert frozen["initial"]["revision"] == 2
    assert frozen["ai_reviews"] == first["ai_reviews"]
    assert frozen["adjudication"]["review"]["claims"] == []
    with pytest.raises(ConflictError, match="整批初判已冻结"):
        save(store, first, revision=2)
    final = completed_review(first)
    final["claims"][0]["status"] = "contradicted"
    final["claims"][0]["severity"] = "major"
    final["claims"][0]["error_types"] = ["other"]
    final["adjudication_reason"] = "Synthetic changed verdict to exercise separate adjudication storage."
    result = save(store, first, final, stage="adjudication")
    assert result["review"]["summary"]["status"] == "failed"
    view = store.get_packet(first["review_id"])
    assert view["initial"]["review"]["claims"][0]["status"] == "supported"
    assert view["adjudication"]["review"]["claims"][0]["status"] == "contradicted"
    assert [item["action"] for item in store.history(first["review_id"])] == ["submit", "freeze", "submit"]


def test_restart_restores_draft_evidence_and_revision(store):
    source = packet()
    store.import_batch("synthetic-test", [source])
    review = completed_review(source)
    review["claims"][0]["status"] = ""
    result = save(store, source, review, submit=False)
    assert result["review"]["summary"]["status"] == "not_evaluated"
    restored = ReviewStore(store.db_path).get_packet(source["review_id"])
    assert restored["initial"]["revision"] == 1
    assert restored["initial"]["review"]["claims"][0]["source_refs"] == review["claims"][0]["source_refs"]
    assert restored["initial"]["state"] == "draft"


def test_duplicate_and_stale_submissions_do_not_create_history(store):
    source = packet()
    store.import_batch("synthetic-test", [source])
    save(store, source, request_id="same-request")
    with pytest.raises(ConflictError, match="重复提交"):
        save(store, source, revision=1, request_id="same-request")
    with pytest.raises(ConflictError, match="其他页面"):
        save(store, source, request_id="different-request")
    assert len(store.history(source["review_id"])) == 1


def test_hash_and_task_identity_cannot_reuse_reviews(store):
    source = packet()
    store.import_batch("synthetic-test", [source])
    save(store, source)
    changed = packet(candidate="The synthetic timeout is 60 s.")
    with pytest.raises(ConflictError, match="旧评审不能复用"):
        store.import_batch("synthetic-test", [changed])
    bad_hash = deepcopy(source)
    bad_hash["artifact_hash"] = "0" * 64
    with pytest.raises(ReviewError, match="SHA-256"):
        store.import_batch("synthetic-test", [bad_hash])
    with pytest.raises(ConflictError, match="候选哈希"):
        store.save_review(source["review_id"], completed_review(source), artifact_hash="0" * 64, expected_revision=1)
    changed_task = deepcopy(source)
    changed_task["task"]["required_facts"][0]["text"] = "Changed requirement"
    with pytest.raises(ConflictError):
        store.import_batch("synthetic-test", [changed_task])


def test_ai_can_arrive_during_blind_review_but_not_change_after_reveal(store):
    source = packet()
    source["ai_reviews"] = []
    store.import_batch("synthetic-test", [source])
    save(store, source, submit=False)
    updated = packet()
    store.import_batch("synthetic-test", [updated])
    assert "ai_reviews" not in store.get_packet(source["review_id"])
    save(store, source, revision=1)
    store.freeze_batch("synthetic-test")
    assert store.get_packet(source["review_id"])["ai_reviews"] == updated["ai_reviews"]
    with pytest.raises(ConflictError, match="更换"):
        store.import_batch("synthetic-test", [source])
    with pytest.raises(ConflictError, match="追加"):
        store.import_batch("synthetic-test", [packet("new-review")])


def test_failed_ai_review_is_retained_but_only_revealed_after_freeze(store):
    source = packet()
    source["ai_reviews"] = [{"judge_id": "failed-judge", "status": "invalid_review", "review": None,
                             "error": "Synthetic invalid JSON review."}]
    source["task"]["rubric"] = {"critical": ["Synthetic critical definition."]}
    source["task"]["output_contract"] = {"forbidden_actions": ["Invent a new duration."]}
    store.import_batch("synthetic-test", [source])
    view = store.get_packet(source["review_id"])
    assert "ai_reviews" not in view
    assert view["task"]["rubric"] == source["task"]["rubric"]
    assert view["task"]["output_contract"] == source["task"]["output_contract"]
    save(store, source)
    store.freeze_batch("synthetic-test")
    view = store.get_packet(source["review_id"])
    assert view["ai_reviews"][0]["review"] is None
    assert view["ai_reviews"][0]["status"] == "invalid_review"


def test_completed_ai_review_cannot_use_null_or_failed_status_with_verdict(store):
    source = packet()
    source["ai_reviews"] = [{"judge_id": "judge", "status": "completed", "review": None}]
    with pytest.raises(ReviewError, match="必须是对象"):
        store.import_batch("synthetic-test", [source])
    source["ai_reviews"][0].update(status="failed", review={"claims": []})
    with pytest.raises(ReviewError, match="不能伪装"):
        store.import_batch("synthetic-test", [source])


@pytest.mark.parametrize("mutation, message", [
    (lambda r: r.update(source_coverage=""), "来源覆盖"),
    (lambda r: r.update(claims=[]), "添加事实声明"),
    (lambda r: r.update(required_facts=[]), "所有预先声明"),
    (lambda r: r["claims"][0].update(justification=""), "非空"),
    (lambda r: r["claims"][0].update(candidate_span="invented quotation"), "候选引文"),
    (lambda r: r["claims"][0].update(source_refs=[{"source_id": "S1", "evidence": "invented evidence"}]), "冻结来源"),
    (lambda r: r["claims"][0].update(source_refs=[]), "来源原文"),
    (lambda r: r["claims"][0].update(status="unsupported", severity=None), "严重程度"),
    (lambda r: r["claims"][0].update(status="unsupported", severity="style_only", error_types=["other"]), "严重程度"),
    (lambda r: r["claims"][0].update(status="unsupported", severity="major", error_types=[]), "错误类型"),
    (lambda r: r["required_facts"][0].update(id="invented-fact"), "增加必需事实"),
])
def test_incomplete_or_fabricated_evidence_rejected(store, mutation, message):
    source = packet()
    store.import_batch("synthetic-test", [source])
    review = completed_review(source)
    mutation(review)
    with pytest.raises(ReviewError, match=message):
        save(store, source, review)
    assert store.history(source["review_id"]) == []


def test_no_claims_requires_explicit_human_confirmation(store):
    source = packet(candidate="Please read the attached synthetic information.")
    source["task"]["required_facts"] = []
    store.import_batch("synthetic-test", [source])
    review = blank_review(source["task"])
    review["source_coverage"] = "adequate"
    with pytest.raises(ReviewError, match="明确确认"):
        save(store, source, review)
    review["no_claims_confirmed"] = True
    assert save(store, source, review)["review"]["summary"]["status"] == "passed"


def test_summary_is_derived_and_uncertain_not_passed(store):
    source = packet()
    store.import_batch("synthetic-test", [source])
    review = completed_review(source)
    review["summary"] = {"status": "passed"}
    review["required_facts"][0]["status"] = "unassessable"
    result = save(store, source, review)
    assert result["review"]["summary"]["status"] == "uncertain"
    review["required_facts"][0].update(status="missing", severity="critical", candidate_span=None, error_types=["required_omission"])
    result = save(store, source, review, revision=1)
    assert result["review"]["summary"]["status"] == "failed"
    assert result["review"]["summary"]["critical_findings"] == 1


def test_final_adjudication_requires_reason(store):
    source = packet()
    store.import_batch("synthetic-test", [source])
    save(store, source)
    store.freeze_batch("synthetic-test")
    with pytest.raises(ReviewError, match="裁决需要"):
        save(store, source, stage="adjudication")


def test_partial_draft_retains_frozen_required_checklist(store):
    source = packet()
    store.import_batch("synthetic-test", [source])
    result = save(store, source, {"claims": [], "required_facts": []}, submit=False)
    assert result["review"]["required_facts"][0]["id"] == "F1"
    assert result["review"]["required_facts"][0]["status"] == ""


def test_incomplete_quoted_evidence_can_be_saved_as_draft_but_not_submitted(store):
    source = packet()
    store.import_batch("synthetic-test", [source])
    review = completed_review(source)
    review["claims"][0]["candidate_span"] = "unfinished quotation"
    review["claims"][0]["source_refs"] = [{"source_id": "", "evidence": "unfinished evidence"}]
    result = save(store, source, review, submit=False)
    assert result["state"] == "draft"
    assert result["review"]["claims"][0]["candidate_span"] == "unfinished quotation"
    with pytest.raises(ReviewError, match="候选引文"):
        save(store, source, review, revision=1)


@pytest.fixture
def service(tmp_path):
    server = build_server(tmp_path / "http.sqlite3", port=0)
    server.store.import_batch("synthetic-test", [packet()])
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


def request(service, method, path, body=None, *, token=True, origin=True, extra_headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", service.server_port, timeout=3)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Review-Token"] = service.csrf_token
    if origin:
        headers["Origin"] = service.origin
    if extra_headers:
        headers.update(extra_headers)
    connection.request(method, path, None if body is None else json.dumps(body), headers)
    response = connection.getresponse()
    result = response.status, dict(response.getheaders()), response.read()
    connection.close()
    return result


def test_http_blind_contract_and_export(service):
    status, headers, content = request(service, "GET", "/api/batches/synthetic-test")
    assert status == 200
    public_id = json.loads(content)["packets"][0]["review_id"]
    status, _, content = request(service, "GET", f"/api/reviews/{public_id}")
    view = json.loads(content)
    assert status == 200 and not view["ai_revealed"]
    assert "ai_reviews" not in view
    status, _, content = request(service, "GET", "/api/batches/synthetic-test/export")
    assert status == 200 and b"hidden-ai-claim" not in content and b"private-model" not in content
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]


def test_http_ai_only_exposes_evidence_and_rejects_human_operations(service):
    source = packet("synthetic-ai-only")
    source["batch_id"] = "synthetic-ai-only"
    listing = service.store.import_batch("synthetic-ai-only", [source], review_mode="ai_only")
    public_id = listing["packets"][0]["review_id"]
    status, _, content = request(service, "GET", f"/api/reviews/{public_id}")
    view = json.loads(content)
    assert status == 200 and view["review_mode"] == "ai_only" and view["ai_revealed"]
    assert view["ai_reviews"] == source["ai_reviews"]
    assert "initial" not in view and "adjudication" not in view
    payload = {"artifact_hash": source["artifact_hash"], "expected_revision": 0, "request_id": "synthetic-ai-only-save",
               "submit": True, "review": completed_review(source)}
    for stage in ("initial", "adjudication"):
        assert request(service, "POST", f"/api/reviews/{public_id}/{stage}", payload)[0] == 409
    assert request(service, "POST", "/api/batches/synthetic-ai-only/freeze", {"expected_revisions": {}})[0] == 409
    status, _, content = request(service, "GET", "/api/batches/synthetic-ai-only/export")
    exported = json.loads(content)
    assert status == 200 and exported["packets"][0]["ai_reviews"] == source["ai_reviews"]
    assert exported["packets"][0]["history"] == []
    assert not service.store.get_packet("hidden-arm-A")["ai_revealed"]


def test_http_valid_save_and_stale_conflict(service):
    source = packet()
    public_id = service.store.list_packets("synthetic-test")["packets"][0]["review_id"]
    payload = {"artifact_hash": source["artifact_hash"], "expected_revision": 0, "request_id": "http-one", "submit": True, "review": completed_review(source)}
    status, _, content = request(service, "POST", f"/api/reviews/{public_id}/initial", payload)
    assert status == 200 and json.loads(content)["revision"] == 1
    payload["request_id"] = "http-two"
    assert request(service, "POST", f"/api/reviews/{public_id}/initial", payload)[0] == 409
    assert request(service, "POST", "/api/batches/synthetic-test/freeze", {"expected_revisions": {public_id: 0}})[0] == 409
    assert request(service, "POST", "/api/batches/synthetic-test/freeze", {"expected_revisions": {public_id: 1}})[0] == 200
    status, _, content = request(service, "GET", f"/api/reviews/{public_id}")
    assert status == 200 and b"hidden-ai-claim" in content
    assert b"private-model" not in content


@pytest.mark.parametrize("options", [
    {"token": False}, {"origin": False},
    {"extra_headers": {"Origin": "https://attacker.example"}},
    {"extra_headers": {"Host": "attacker.example"}},
    {"extra_headers": {"Sec-Fetch-Site": "cross-site"}},
])
def test_http_mutations_require_local_origin_and_token(service, options):
    assert request(service, "POST", "/api/batches/synthetic-test/freeze", {}, **options)[0] == 403
    assert service.store.list_packets("synthetic-test")["batch"]["state"] == "open"


def test_cross_site_post_with_delayed_body_returns_403_without_socket_reset(service):
    connection = http.client.HTTPConnection("127.0.0.1", service.server_port, timeout=3)
    try:
        # A client can send headers before the body reaches the server, including on loopback.
        connection.putrequest("POST", "/api/batches/synthetic-test/freeze")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", "2")
        connection.putheader("Origin", service.origin)
        connection.putheader("X-Review-Token", service.csrf_token)
        connection.putheader("Sec-Fetch-Site", "cross-site")
        connection.endheaders()
        time.sleep(0.02)
        connection.send(b"{}")
        response = connection.getresponse()
        assert response.status == 403
        assert json.loads(response.read())["error"] == "拒绝跨站请求。"
    finally:
        connection.close()
    assert service.store.list_packets("synthetic-test")["batch"]["state"] == "open"


@pytest.mark.parametrize("length", ["2", "invalid", "-1", str(MAX_BODY_BYTES + 1)])
def test_rejected_post_does_not_wait_indefinitely_for_body(service, length):
    # Read through EOF: a 403 alone does not prove the handler stopped waiting for a body.
    with socket.create_connection(("127.0.0.1", service.server_port), timeout=1.5) as connection:
        headers = (f"POST /api/batches/synthetic-test/freeze HTTP/1.1\r\n"
                   f"Host: {service.authority}\r\nContent-Type: application/json\r\n"
                   f"Content-Length: {length}\r\nSec-Fetch-Site: cross-site\r\n\r\n")
        connection.sendall(headers.encode("ascii"))
        response = bytearray()
        while chunk := connection.recv(4096):
            response.extend(chunk)
    assert response.startswith(b"HTTP/1.0 403 ")
    assert json.loads(response.split(b"\r\n\r\n", 1)[1])["error"] == "拒绝跨站请求。"
    assert service.store.list_packets("synthetic-test")["batch"]["state"] == "open"


def test_external_top_level_navigation_allowed_but_cross_site_api_read_rejected(service):
    navigation = {"Sec-Fetch-Site": "cross-site", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document"}
    assert request(service, "GET", "/", origin=False, extra_headers=navigation)[0] == 200
    assert request(service, "GET", "/api/session", origin=False, extra_headers=navigation)[0] == 403
    assert request(service, "GET", "/api/batches", origin=False, extra_headers=navigation)[0] == 403


def test_static_serving_has_no_filesystem_escape_and_no_inline_html_data(service):
    attack = "<img src=x onerror=alert('candidate')><script>window.syntheticXss=true</script>"
    source = packet("xss", candidate=attack)
    source["task"]["sources"][0]["text"] = attack
    service.store.import_batch("synthetic-test", [source])
    status, headers, content = request(service, "GET", "/")
    assert status == 200 and attack.encode() not in content
    assert headers["Content-Type"].startswith("text/html")
    status, _, javascript = request(service, "GET", "/app.js")
    assert status == 200
    # The static client renders every untrusted string with textContent/value, never HTML insertion.
    for sink in (b"innerHTML", b"outerHTML", b"insertAdjacentHTML", b"document.write", b"eval("):
        assert sink not in javascript
    assert b"node.textContent = text" in javascript
    for path in ("/../review_store.py", "/%2e%2e/review_store.py", "/api/../../review_store.py"):
        assert request(service, "GET", path)[0] == 404
    view = service.store.get_packet("xss")
    assert view["candidate_text"] == attack


def test_server_rejects_non_loopback_binding(tmp_path):
    with pytest.raises(ValueError, match="127.0.0.1"):
        build_server(tmp_path / "unused.sqlite3", host="0.0.0.0", port=0)


def test_anonymized_export_keeps_both_stages_and_complete_history(store):
    source = packet()
    store.import_batch("synthetic-test", [source])
    save(store, source, submit=False)
    save(store, source, revision=1)
    store.freeze_batch("synthetic-test")
    final = completed_review(source)
    final["adjudication_reason"] = "Reviewed synthetic evidence; retain initial judgment."
    save(store, source, final, stage="adjudication")
    exported = store.export_batch("synthetic-test")
    assert exported["anonymized"] is True
    entry = exported["packets"][0]
    assert entry["initial"]["state"] == "frozen" and entry["adjudication"]["state"] == "submitted"
    assert len(entry["history"]) == 4
    assert "private" not in entry and "internal_review_id" not in entry
    internal = store.export_batch("synthetic-test", include_private=True)
    assert internal["anonymized"] is False
    assert internal["packets"][0]["private"]["writer_model"] == "private-model"
