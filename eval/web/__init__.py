"""Local-only review HTTP service, using only the Python standard library."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import logging
from pathlib import Path
import secrets
import threading
from urllib.parse import unquote, urlsplit

from ..review_store import ReviewError, ReviewStore


ASSETS = Path(__file__).parent
MAX_BODY_BYTES = 2 * 1024 * 1024


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 中存在重复字段。")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"不允许非有限 JSON 数值：{value}")


class ReviewHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store):
        self.store = store
        self.csrf_token = secrets.token_urlsafe(32)
        super().__init__(address, ReviewHandler)
        self.authority = f"127.0.0.1:{self.server_port}"
        self.origin = f"http://{self.authority}"


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = "TextPrisonReview/0.2"

    def log_message(self, format, *args):
        logging.getLogger("textprison.review").info(format, *args)

    def _send(self, status, body, content_type="application/json; charset=utf-8", *, download=False):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        if download:
            self.send_header("Content-Disposition", 'attachment; filename="textprison-review.json"')
        self.end_headers()
        self.wfile.write(body)

    def _security(self, *, mutation=False):
        if self.headers.get("Host") != self.server.authority:
            self._send(403, {"error": "Host 与本地评审服务不匹配。"})
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin != self.server.origin:
            self._send(403, {"error": "仅允许同源请求。"})
            return False
        top_level_navigation = (not mutation and self.command == "GET" and urlsplit(self.path).path == "/"
                                and self.headers.get("Sec-Fetch-Mode") == "navigate"
                                and self.headers.get("Sec-Fetch-Dest") == "document")
        if self.headers.get("Sec-Fetch-Site") not in {None, "same-origin", "none"} and not top_level_navigation:
            self._send(403, {"error": "拒绝跨站请求。"})
            return False
        if mutation:
            token = self.headers.get("X-Review-Token", "")
            if origin != self.server.origin or not hmac.compare_digest(token.encode("utf-8"), self.server.csrf_token.encode("ascii")):
                self._send(403, {"error": "写入请求缺少有效的同源会话令牌，请刷新页面。"})
                return False
        return True

    def _parts(self):
        parsed = urlsplit(self.path)
        if parsed.query or parsed.fragment:
            raise ReviewError("此接口不接受查询参数。")
        return [unquote(part) for part in parsed.path.split("/") if part]

    def _dispatch_error(self, error):
        if isinstance(error, ReviewError):
            self._send(error.status, {"error": str(error)})
        elif isinstance(error, (ValueError, UnicodeError)):
            self._send(400, {"error": str(error)})
        else:
            logging.getLogger("textprison.review").exception("Review request failed")
            self._send(500, {"error": "评审服务内部错误；草稿未确认保存，请查看服务日志。"})

    def do_GET(self):
        if not self._security():
            return
        try:
            parts = self._parts()
            assets = {(): ("index.html", "text/html; charset=utf-8"),
                      ("app.js",): ("app.js", "text/javascript; charset=utf-8"),
                      ("style.css",): ("style.css", "text/css; charset=utf-8")}
            if tuple(parts) in assets:
                filename, content_type = assets[tuple(parts)]
                self._send(200, (ASSETS / filename).read_bytes(), content_type)
            elif parts == ["api", "session"]:
                self._send(200, {"token": self.server.csrf_token, "version": "0.2"})
            elif parts == ["api", "batches"]:
                self._send(200, {"batches": self.server.store.list_batches()})
            elif len(parts) == 3 and parts[:2] == ["api", "batches"]:
                self._send(200, self.server.store.list_packets(parts[2]))
            elif len(parts) == 4 and parts[:2] == ["api", "batches"] and parts[3] == "export":
                self._send(200, self.server.store.export_batch(parts[2]), download=True)
            elif len(parts) == 3 and parts[:2] == ["api", "reviews"]:
                self._send(200, self.server.store.get_packet(parts[2]))
            elif len(parts) == 4 and parts[:2] == ["api", "reviews"] and parts[3] == "history":
                self._send(200, {"history": self.server.store.history(parts[2])})
            else:
                self._send(404, {"error": "接口不存在。"})
        except Exception as error:
            self._dispatch_error(error)

    def _body(self):
        if self.headers.get_content_type() != "application/json":
            raise ReviewError("写入接口仅接受 application/json。")
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError as error:
            raise ReviewError("Content-Length 无效。") from error
        if length < 0 or length > MAX_BODY_BYTES:
            raise ReviewError("请求体为空或超过 2 MiB 限制。")
        data = self.rfile.read(length)
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        if not isinstance(value, dict):
            raise ReviewError("请求体必须是 JSON 对象。")
        return value

    def do_POST(self):
        if not self._security(mutation=True):
            return
        try:
            parts = self._parts()
            data = self._body()
            if len(parts) == 4 and parts[:2] == ["api", "reviews"] and parts[3] in {"initial", "adjudication"}:
                if not isinstance(data.get("request_id"), str) or not data["request_id"].strip():
                    raise ReviewError("写入需要 request_id。")
                result = self.server.store.save_review(
                    parts[2], data.get("review"), stage=parts[3],
                    artifact_hash=data.get("artifact_hash"), expected_revision=data.get("expected_revision"),
                    submit=data.get("submit", False), request_id=data["request_id"],
                )
                self._send(200, result)
            elif len(parts) == 4 and parts[:2] == ["api", "batches"] and parts[3] == "freeze":
                if not isinstance(data.get("expected_revisions"), dict):
                    raise ReviewError("冻结请求需要当前批次的 expected_revisions。")
                self._send(200, self.server.store.freeze_batch(parts[2], expected_revisions=data["expected_revisions"]))
            elif parts == ["api", "shutdown"]:
                self._send(200, {"stopped": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
            else:
                self._send(404, {"error": "接口不存在。"})
        except Exception as error:
            self._dispatch_error(error)


def build_server(db_path, host="127.0.0.1", port=8765):
    """Build without starting; port=0 is useful for isolated HTTP tests."""
    if host != "127.0.0.1":
        raise ValueError("人工评审服务仅允许绑定 127.0.0.1。")
    return ReviewHTTPServer((host, port), ReviewStore(db_path))


def serve(db_path, host="127.0.0.1", port=8765):
    """Serve until Ctrl+C or the authenticated local shutdown request."""
    with build_server(db_path, host, port) as server:
        print(f"TextPrison 人工评审：{server.origin}（Ctrl+C 停止）", flush=True)
        try:
            server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            pass
