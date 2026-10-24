"""Versioned, blind human review storage. Model verdicts never fill human forms."""

from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid


class ReviewError(ValueError):
    status = 400


class ConflictError(ReviewError):
    status = 409


class NotFoundError(ReviewError):
    status = 404


CLAIM_STATUSES = {"supported", "contradicted", "unsupported", "unassessable"}
FACT_STATUSES = {"preserved", "missing", "altered", "unassessable"}
SEVERITIES = {"critical", "major", "minor", "style_only"}
ERROR_TYPES = {"negation", "modality", "condition", "scope", "causality", "actor_object",
               "quantity_unit", "time_version", "citation", "unsupported_addition", "required_omission",
               "permission", "execution", "other"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def _string(value, field, *, required=False):
    if not isinstance(value, str) or (required and not value.strip()):
        raise ReviewError(f"{field} 必须是{'非空' if required else ''}文本。")
    return value


def _list(value, field):
    if not isinstance(value, list):
        raise ReviewError(f"{field} 必须是数组。")
    return value


def _object(value, field):
    if not isinstance(value, dict):
        raise ReviewError(f"{field} 必须是对象。")
    return value


def blank_review(task):
    """Return an empty human form with only predeclared required facts."""
    return {
        "review_version": "0.2", "source_coverage": "", "coverage_note": "",
        "claims": [], "no_claims_confirmed": False,
        "required_facts": [
            {"id": fact["id"], "status": "", "candidate_span": None,
             "source_refs": [], "severity": None, "error_types": [], "justification": ""}
            for fact in task.get("required_facts", [])
        ],
        "uncertain_items": [], "adjudication_reason": "",
    }


def _packet(packet, batch_id):
    _object(packet, "packet")
    if packet.get("batch_id", batch_id) != batch_id:
        raise ReviewError("候选的 batch_id 与导入批次不一致。")
    review_id = _string(packet.get("review_id"), "review_id", required=True)
    candidate = _string(packet.get("candidate_text"), "candidate_text", required=True)
    artifact_hash = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
    if packet.get("artifact_hash") != artifact_hash:
        raise ReviewError("artifact_hash 必须匹配候选文本 UTF-8 的 SHA-256。")
    raw_task = _object(packet.get("task"), "task")
    task = {}
    for name in ("id", "scenario_id", "profile", "language", "prompt"):
        task[name] = _string(raw_task.get(name, ""), f"task.{name}", required=name == "prompt")
    for name in ("sources", "required_facts"):
        task[name] = []
        seen = set()
        for item in _list(raw_task.get(name, []), f"task.{name}"):
            _object(item, name)
            item_id = _string(item.get("id"), f"{name}.id", required=True)
            if item_id in seen:
                raise ReviewError(f"{name} ID 重复：{item_id}")
            seen.add(item_id)
            task[name].append({"id": item_id, "text": _string(item.get("text"), f"{name}.text", required=True)})
    task["allowed_transformations"] = [
        _string(item, "allowed_transformations", required=True)
        for item in _list(raw_task.get("allowed_transformations", []), "allowed_transformations")
    ]
    # Supplied public task requirements are frozen data, not AI-derived human answers.
    for name in ("rubric", "severity_rubric", "output_contract"):
        if name not in raw_task:
            continue
        rubric = raw_task[name]
        if not isinstance(rubric, (str, dict, list)):
            raise ReviewError(f"{name} 格式错误。")
        task[name] = rubric
    for name in ("synthetic", "executable"):
        if name in raw_task:
            if not isinstance(raw_task[name], bool):
                raise ReviewError(f"{name} 必须是布尔值。")
            task[name] = raw_task[name]
    ai_reviews = _list(packet.get("ai_reviews", []), "ai_reviews")
    for review in ai_reviews:
        _object(review, "ai_reviews entry")
        _string(review.get("judge_id"), "judge_id", required=True)
        if review.get("status", "completed") == "completed":
            _object(review.get("review"), "AI review")
        else:
            _string(review.get("status"), "AI review status", required=True)
            if review.get("review") is not None:
                raise ReviewError("失败或未完成的 AI 评审必须使用 review: null，不能伪装为有效意见。")
            if "error" in review:
                _string(review["error"], "AI review error")
    return {
        "review_id": review_id, "batch_id": batch_id, "artifact_hash": artifact_hash,
        "candidate_text": candidate,
        "original_text": _string(packet.get("original_text") or "", "original_text"),
        "task": task, "private": _object(packet.get("private", {}), "private"),
        "ai_reviews": ai_reviews,
    }


def _validate_review(payload, packet, *, submitted, stage):
    _object(payload, "review")
    if payload.get("review_version", "0.2") != "0.2":
        raise ReviewError("仅支持人工评审格式 0.2。")
    task = packet["task"]
    result = blank_review(task)
    coverage = payload.get("source_coverage", "")
    if coverage not in {"", "adequate", "partial", "insufficient"}:
        raise ReviewError("来源覆盖状态无效。")
    if submitted and not coverage:
        raise ReviewError("提交前请判断来源覆盖情况。")
    result["source_coverage"] = coverage
    result["coverage_note"] = _string(payload.get("coverage_note", ""), "coverage_note")
    if submitted and coverage in {"partial", "insufficient"} and not result["coverage_note"].strip():
        raise ReviewError("来源不完整时，请说明缺少的证据。")
    no_claims = payload.get("no_claims_confirmed", False)
    if not isinstance(no_claims, bool):
        raise ReviewError("no_claims_confirmed 必须是布尔值。")
    result["no_claims_confirmed"] = no_claims
    source_map = {item["id"]: item["text"] for item in task["sources"]}
    required_ids = {item["id"] for item in task["required_facts"]}
    for field, statuses in (("claims", CLAIM_STATUSES), ("required_facts", FACT_STATUSES)):
        rows = []
        seen = set()
        for item in _list(payload.get(field, []), field):
            _object(item, field)
            item_id = _string(item.get("id"), f"{field}.id", required=True)
            if item_id in seen:
                raise ReviewError(f"{field} ID 重复。")
            seen.add(item_id)
            if field == "required_facts" and item_id not in required_ids:
                raise ReviewError("不得在阅读候选后增加必需事实。")
            row = {"id": item_id}
            if field == "claims":
                row["text"] = _string(item.get("text", ""), "claim.text", required=submitted)
            status = item.get("status", "")
            if status not in statuses | {""} or (submitted and not status):
                raise ReviewError(f"{item_id} 尚未完成状态判断。")
            row["status"] = status
            span = item.get("candidate_span")
            if span == "":
                span = None
            if span is not None:
                _string(span, "candidate_span")
                if submitted and span not in packet["candidate_text"]:
                    raise ReviewError(f"{item_id} 的候选引文不在当前候选文本中。")
            if submitted and (field == "claims" or status in {"preserved", "altered"}) and span is None:
                raise ReviewError(f"{item_id} 需要候选原文引文。")
            if submitted and status == "missing" and span is not None:
                raise ReviewError("缺失事实的候选引文应留空。")
            row["candidate_span"] = span
            severity = item.get("severity") or None
            if severity is not None and severity not in SEVERITIES:
                raise ReviewError("严重程度无效。")
            if submitted and status in {"contradicted", "unsupported", "missing", "altered"} and severity not in {"critical", "major", "minor"}:
                raise ReviewError(f"{item_id} 的语义错误需要 critical、major 或 minor 严重程度。")
            row["severity"] = severity
            error_types = _list(item.get("error_types", []), "error_types")
            if any(not isinstance(kind, str) or kind not in ERROR_TYPES for kind in error_types):
                raise ReviewError("错误类型无效。")
            if len(set(error_types)) != len(error_types):
                raise ReviewError("错误类型不能重复。")
            if submitted and status in {"contradicted", "unsupported", "missing", "altered"} and not error_types:
                raise ReviewError(f"{item_id} 的已确认错误需要至少一种错误类型。")
            row["error_types"] = error_types
            row["justification"] = _string(item.get("justification", ""), "justification", required=submitted)
            row["source_refs"] = []
            for ref in _list(item.get("source_refs", []), "source_refs"):
                _object(ref, "source_ref")
                source_id = _string(ref.get("source_id"), "source_id", required=submitted)
                if source_id and source_id not in source_map:
                    raise ReviewError(f"未知来源：{source_id}")
                evidence = _string(ref.get("evidence", ""), "evidence")
                if submitted and evidence and evidence not in source_map[source_id]:
                    raise ReviewError(f"{source_id} 的证据引文不在冻结来源中。")
                row["source_refs"].append({"source_id": source_id, "evidence": evidence})
            if submitted and status in {"supported", "contradicted", "preserved", "altered"}:
                if not any(ref["evidence"] for ref in row["source_refs"]):
                    raise ReviewError(f"{item_id} 需要来源原文证据。")
            rows.append(row)
        if field == "required_facts" and submitted and seen != required_ids:
            raise ReviewError("提交前必须逐项评价所有预先声明的必需事实。")
        if field == "required_facts" and not submitted:
            # Partial API drafts must not remove the predeclared checklist from the UI.
            by_id = {row["id"]: row for row in rows}
            rows = [by_id.get(row["id"], row) for row in blank_review(task)["required_facts"]]
        result[field] = rows
    if result["claims"] and no_claims:
        raise ReviewError("已有声明时不能确认“没有可评价的事实声明”。")
    if submitted and not result["claims"] and not no_claims:
        raise ReviewError("请添加事实声明，或明确确认候选不包含可评价的事实声明。")
    result["uncertain_items"] = []
    for item in _list(payload.get("uncertain_items", []), "uncertain_items"):
        _object(item, "uncertain_item")
        result["uncertain_items"].append({
            "text": _string(item.get("text", ""), "uncertain.text", required=submitted),
            "evidence_needed": _string(item.get("evidence_needed", ""), "uncertain.evidence_needed", required=submitted),
        })
    result["adjudication_reason"] = _string(payload.get("adjudication_reason", ""), "adjudication_reason")
    if submitted and stage == "adjudication" and not result["adjudication_reason"].strip():
        raise ReviewError("最终裁决需要说明采纳、修改或维持初判的理由。")
    claim_counts = Counter(row["status"] or "pending" for row in result["claims"])
    fact_counts = Counter(row["status"] or "pending" for row in result["required_facts"])
    failed = any(claim_counts[s] for s in ("contradicted", "unsupported")) or any(fact_counts[s] for s in ("missing", "altered"))
    uncertain = coverage != "adequate" or claim_counts["unassessable"] or fact_counts["unassessable"] or bool(result["uncertain_items"])
    if not submitted:
        status = "not_evaluated"
    elif failed:
        status = "failed"
    elif coverage == "insufficient":
        status = "not_evaluated"
    elif uncertain:
        status = "uncertain"
    else:
        status = "passed"
    result["summary"] = {
        "status": status, "claims": dict(claim_counts), "required_facts": dict(fact_counts),
        "required_fact_total": len(required_ids),
        "critical_findings": sum(row["severity"] == "critical" and row["status"] in {"contradicted", "unsupported", "missing", "altered"}
                                 for row in result["claims"] + result["required_facts"]),
        "derived_by": "review_store", "complete": submitted,
    }
    return result


class ReviewStore:
    """Each write is transactional and requires the caller's current revision."""

    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS batches (
                    batch_id TEXT PRIMARY KEY, state TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL, frozen_at TEXT
                );
                CREATE TABLE IF NOT EXISTS packets (
                    review_id TEXT PRIMARY KEY, public_id TEXT UNIQUE NOT NULL,
                    batch_id TEXT NOT NULL REFERENCES batches(batch_id),
                    artifact_hash TEXT NOT NULL, packet_json TEXT NOT NULL, ordinal INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS human_reviews (
                    review_id TEXT NOT NULL REFERENCES packets(review_id), stage TEXT NOT NULL,
                    revision INTEGER NOT NULL, state TEXT NOT NULL, payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL, PRIMARY KEY (review_id, stage)
                );
                CREATE TABLE IF NOT EXISTS review_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT, review_id TEXT NOT NULL,
                    stage TEXT NOT NULL, revision INTEGER NOT NULL, action TEXT NOT NULL,
                    payload_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS requests (
                    request_id TEXT PRIMARY KEY, created_at TEXT NOT NULL
                );
            """)

    @contextmanager
    def _connection(self, *, write=False):
        db = sqlite3.connect(str(self.db_path), timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _row(db, identifier):
        row = db.execute("SELECT * FROM packets WHERE public_id = ? OR review_id = ?", (identifier, identifier)).fetchone()
        if row is None:
            raise NotFoundError("候选不存在。")
        return row

    def import_batch(self, batch_id, packets):
        _string(batch_id, "batch_id", required=True)
        normalized = [_packet(item, batch_id) for item in _list(packets, "packets")]
        if not normalized:
            raise ReviewError("不能导入空批次。")
        if len({item["review_id"] for item in normalized}) != len(normalized):
            raise ReviewError("导入批次中存在重复 review_id。")
        with self._connection(write=True) as db:
            db.execute("INSERT OR IGNORE INTO batches(batch_id, created_at) VALUES (?, ?)", (batch_id, _now()))
            batch = db.execute("SELECT * FROM batches WHERE batch_id = ?", (batch_id,)).fetchone()
            ordinal = db.execute("SELECT COALESCE(MAX(ordinal), 0) FROM packets WHERE batch_id = ?", (batch_id,)).fetchone()[0]
            for packet in normalized:
                old = db.execute("SELECT * FROM packets WHERE review_id = ?", (packet["review_id"],)).fetchone()
                if old:
                    previous = json.loads(old["packet_json"])
                    immutable = ("batch_id", "artifact_hash", "candidate_text", "original_text", "task", "private")
                    if any(previous[key] != packet[key] for key in immutable):
                        raise ConflictError("候选或冻结任务已改变；必须使用新的 review_id，旧评审不能复用。")
                    if previous["ai_reviews"] != packet["ai_reviews"]:
                        if batch["state"] == "frozen":
                            raise ConflictError("批次已冻结，不能更换已揭示的 AI 评审。")
                        db.execute("UPDATE packets SET packet_json = ? WHERE review_id = ?", (_json(packet), packet["review_id"]))
                else:
                    if batch["state"] == "frozen":
                        raise ConflictError("批次已冻结，不能追加候选。")
                    ordinal += 1
                    db.execute("INSERT INTO packets VALUES (?, ?, ?, ?, ?, ?)",
                               (packet["review_id"], uuid.uuid4().hex, batch_id, packet["artifact_hash"], _json(packet), ordinal))
        return self.list_packets(batch_id)

    def list_batches(self):
        with self._connection() as db:
            return [dict(row) for row in db.execute("""
                SELECT b.*, COUNT(p.review_id) AS total,
                    SUM(CASE WHEN i.state IN ('submitted', 'frozen') THEN 1 ELSE 0 END) AS initial_submitted,
                    SUM(CASE WHEN a.state = 'submitted' THEN 1 ELSE 0 END) AS adjudication_submitted
                FROM batches b LEFT JOIN packets p ON p.batch_id = b.batch_id
                LEFT JOIN human_reviews i ON i.review_id = p.review_id AND i.stage = 'initial'
                LEFT JOIN human_reviews a ON a.review_id = p.review_id AND a.stage = 'adjudication'
                GROUP BY b.batch_id ORDER BY b.created_at, b.batch_id
            """)]

    def list_packets(self, batch_id):
        with self._connection() as db:
            batch = db.execute("SELECT * FROM batches WHERE batch_id = ?", (batch_id,)).fetchone()
            if batch is None:
                raise NotFoundError("批次不存在。")
            rows = db.execute("SELECT * FROM packets WHERE batch_id = ? ORDER BY ordinal", (batch_id,)).fetchall()
            result = []
            for row in rows:
                records = {r["stage"]: dict(r) for r in db.execute("SELECT stage, revision, state FROM human_reviews WHERE review_id = ?", (row["review_id"],))}
                result.append({"review_id": row["public_id"], "label": f"候选 {row['ordinal']:02d}",
                               "initial": records.get("initial", {"stage": "initial", "revision": 0, "state": "empty"}),
                               "adjudication": records.get("adjudication", {"stage": "adjudication", "revision": 0, "state": "empty"})})
            return {"batch": dict(batch), "packets": result}

    @staticmethod
    def _record(db, row, stage):
        record = db.execute("SELECT * FROM human_reviews WHERE review_id = ? AND stage = ?", (row["review_id"], stage)).fetchone()
        if record is None:
            return {"revision": 0, "state": "empty", "updated_at": None,
                    "review": blank_review(json.loads(row["packet_json"])["task"])}
        return {"revision": record["revision"], "state": record["state"], "updated_at": record["updated_at"],
                "review": json.loads(record["payload_json"])}

    def _view(self, db, row):
        packet = json.loads(row["packet_json"])
        batch = db.execute("SELECT * FROM batches WHERE batch_id = ?", (row["batch_id"],)).fetchone()
        revealed = batch["state"] == "frozen"
        public_task = dict(packet["task"])
        # IDs supplied by the experiment may encode assignments; only source/fact IDs are needed for evidence.
        public_task.pop("id", None)
        public_task.pop("scenario_id", None)
        view = {"review_id": row["public_id"], "batch_id": row["batch_id"], "label": f"候选 {row['ordinal']:02d}",
                "artifact_hash": packet["artifact_hash"], "candidate_text": packet["candidate_text"],
                "original_text": packet["original_text"], "task": public_task,
                "batch_state": batch["state"], "ai_revealed": revealed,
                "initial": self._record(db, row, "initial")}
        if revealed:
            view["ai_reviews"] = packet["ai_reviews"]
            view["adjudication"] = self._record(db, row, "adjudication")
        return view

    def get_packet(self, review_id):
        with self._connection() as db:
            return self._view(db, self._row(db, review_id))

    def save_review(self, review_id, payload, *, artifact_hash, expected_revision,
                    stage="initial", submit=False, request_id=None):
        if stage not in {"initial", "adjudication"}:
            raise ReviewError("评审阶段无效。")
        if type(expected_revision) is not int or expected_revision < 0:
            raise ReviewError("expected_revision 必须是非负整数。")
        if type(submit) is not bool:
            raise ReviewError("submit 必须是布尔值。")
        with self._connection(write=True) as db:
            if request_id is not None:
                _string(request_id, "request_id", required=True)
                if db.execute("SELECT 1 FROM requests WHERE request_id = ?", (request_id,)).fetchone():
                    raise ConflictError("重复提交已被拒绝；请重新载入当前版本。")
            row = self._row(db, review_id)
            if artifact_hash != row["artifact_hash"]:
                raise ConflictError("候选哈希不一致，不能保存到旧评审。")
            batch = db.execute("SELECT state FROM batches WHERE batch_id = ?", (row["batch_id"],)).fetchone()
            if stage == "initial" and batch["state"] == "frozen":
                raise ConflictError("整批初判已冻结，请在最终裁决中记录更改。")
            if stage == "adjudication" and batch["state"] != "frozen":
                raise ConflictError("整批初判冻结后才能开始最终裁决。")
            current = self._record(db, row, stage)
            if current["revision"] != expected_revision:
                raise ConflictError("此评审已在其他页面修改；请保留当前文字并重新载入。")
            result = _validate_review(payload, json.loads(row["packet_json"]), submitted=submit, stage=stage)
            revision, state, now = expected_revision + 1, "submitted" if submit else "draft", _now()
            db.execute("""INSERT INTO human_reviews VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(review_id, stage) DO UPDATE SET revision=excluded.revision,
                       state=excluded.state, payload_json=excluded.payload_json, updated_at=excluded.updated_at""",
                       (row["review_id"], stage, revision, state, _json(result), now))
            db.execute("INSERT INTO review_history(review_id, stage, revision, action, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                       (row["review_id"], stage, revision, "submit" if submit else "save_draft", _json(result), now))
            if request_id is not None:
                db.execute("INSERT INTO requests VALUES (?, ?)", (request_id, now))
            return {"revision": revision, "state": state, "updated_at": now, "review": result}

    def freeze_batch(self, batch_id, *, expected_revisions=None):
        with self._connection(write=True) as db:
            batch = db.execute("SELECT * FROM batches WHERE batch_id = ?", (batch_id,)).fetchone()
            if batch is None:
                raise NotFoundError("批次不存在。")
            if batch["state"] == "frozen":
                raise ConflictError("批次已经冻结。")
            rows = db.execute("""SELECT p.review_id, p.public_id, r.revision, r.state, r.payload_json
                               FROM packets p LEFT JOIN human_reviews r
                               ON r.review_id=p.review_id AND r.stage='initial' WHERE p.batch_id=?""", (batch_id,)).fetchall()
            if not rows or any(row["state"] != "submitted" for row in rows):
                raise ConflictError("必须先提交本批次每一份独立初判，才能冻结并查看 AI 证据。")
            if expected_revisions is not None:
                _object(expected_revisions, "expected_revisions")
                actual = {row["public_id"]: row["revision"] for row in rows}
                if expected_revisions != actual:
                    raise ConflictError("批次或初判版本已改变，请重新载入后再冻结。")
            now = _now()
            for row in rows:
                revision = row["revision"] + 1
                db.execute("UPDATE human_reviews SET revision=?, state='frozen', updated_at=? WHERE review_id=? AND stage='initial'",
                           (revision, now, row["review_id"]))
                db.execute("INSERT INTO review_history(review_id, stage, revision, action, payload_json, created_at) VALUES (?, 'initial', ?, 'freeze', ?, ?)",
                           (row["review_id"], revision, row["payload_json"], now))
            db.execute("UPDATE batches SET state='frozen', frozen_at=? WHERE batch_id=?", (now, batch_id))
        return self.list_packets(batch_id)

    @staticmethod
    def _history(db, row):
        return [{"stage": item["stage"], "revision": item["revision"], "action": item["action"],
                 "created_at": item["created_at"], "review": json.loads(item["payload_json"])}
                for item in db.execute("SELECT * FROM review_history WHERE review_id=? ORDER BY history_id", (row["review_id"],))]

    def history(self, review_id):
        with self._connection() as db:
            return self._history(db, self._row(db, review_id))

    def export_batch(self, batch_id, *, include_private=False):
        # One read transaction keeps stages, batch state and history from the same snapshot.
        with self._connection() as db:
            batch = db.execute("SELECT * FROM batches WHERE batch_id=?", (batch_id,)).fetchone()
            if batch is None:
                raise NotFoundError("批次不存在。")
            packets = []
            for row in db.execute("SELECT * FROM packets WHERE batch_id=? ORDER BY ordinal", (batch_id,)).fetchall():
                public = self._view(db, row)
                public["history"] = self._history(db, row)
                if include_private:
                    packet = json.loads(row["packet_json"])
                    public["internal_review_id"] = row["review_id"]
                    public["private"] = packet["private"]
                    public["task"]["id"] = packet["task"]["id"]
                    public["task"]["scenario_id"] = packet["task"]["scenario_id"]
                packets.append(public)
        return {"export_version": "0.2", "exported_at": _now(), "anonymized": not include_private,
                "batch": dict(batch), "packets": packets,
                "interpretation": "initial 为冻结的独立人工初判；adjudication 为查看 AI 后的人工裁决。AI 结果不代表人工结论。"}
