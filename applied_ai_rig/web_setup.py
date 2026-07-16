import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import webbrowser
from collections.abc import Sequence
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

from . import __version__
from .installer import FileStatus, InstallationPlan, build_plan, unified_diff
from .intake import MODULE_IDS, MODULE_INFO, QUESTIONS, SETUP_PROFILES, recommend_modules
from .manifest import Profile


MAX_REQUEST_BYTES = 64 * 1024
def _security_policy(nonce: str) -> str:
    return (
        "default-src 'none'; "
        f"style-src 'nonce-{nonce}'; "
        f"script-src 'nonce-{nonce}'; "
        "connect-src 'self'; "
        "img-src 'self' data:; "
        "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    )


@dataclass(frozen=True)
class WebSetupResult:
    profile: Profile
    approved_paths: frozenset[str]
    plan_digest: str


class WebSetupCancelled(RuntimeError):
    """Raised when the local browser session is cancelled."""


class WebSetupSession:
    def __init__(
        self,
        target: Path,
        template_root: Path,
        known_checksums: Mapping[str, str],
        previous: Profile | None = None,
        known_manual_integrations: Sequence[str] = (),
    ) -> None:
        self.target = target
        self.template_root = template_root
        self.known_checksums = dict(known_checksums)
        self.previous = previous
        self.known_manual_integrations = tuple(known_manual_integrations)
        self.token = secrets.token_urlsafe(24)
        self.csp_nonce = secrets.token_urlsafe(24)
        self.result: WebSetupResult | None = None
        self.cancelled = False

    def build_plan(self, payload: object) -> InstallationPlan:
        profile = profile_from_web_payload(payload, self.previous)
        return build_plan(
            self.target,
            profile,
            self.template_root,
            self.known_checksums,
            self.known_manual_integrations,
        )


def _require_dict(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected {label} to be an object")
    if any(not isinstance(key, str) for key in value):
        raise ValueError(f"Expected {label} keys to be strings")
    return dict(value)


def profile_from_web_payload(
    payload: object,
    previous: Profile | None = None,
) -> Profile:
    data = _require_dict(payload, "profile")
    if set(data) != {"route", "answers", "selected_modules"}:
        raise ValueError("Expected route, answers, and selected_modules")

    route = data["route"]
    if not isinstance(route, str) or route not in (*SETUP_PROFILES, "custom", "existing"):
        raise ValueError("Unknown setup route")

    answers_raw = _require_dict(data["answers"], "answers")
    question_ids = {question.id for question in QUESTIONS}
    if route == "existing":
        if previous is None:
            raise ValueError("No existing profile is available")
        if answers_raw:
            raise ValueError("The existing route must not replace recorded answers")
        answers = dict(previous.answers)
        reasons = dict(previous.recommendation_reasons)
    elif route == "custom":
        if set(answers_raw) != question_ids:
            raise ValueError("Custom answers must include every assessment question")
        if any(not isinstance(value, bool) for value in answers_raw.values()):
            raise ValueError("Assessment answers must be booleans")
        answers = {key: bool(value) for key, value in answers_raw.items()}
        reasons = recommend_modules(answers)
    else:
        if answers_raw:
            raise ValueError("Quick profiles must not contain factual answers")
        answers = {}
        reasons = {
            module_id: "Selected by the named setup profile; review whether it applies to this project."
            for module_id in SETUP_PROFILES[route]
        }

    modules_raw = data["selected_modules"]
    if not isinstance(modules_raw, list) or any(
        not isinstance(module_id, str) for module_id in modules_raw
    ):
        raise ValueError("selected_modules must be a list of module IDs")
    if len(modules_raw) != len(set(modules_raw)):
        raise ValueError("Selected module IDs must be unique")
    unknown = set(modules_raw) - set(MODULE_IDS)
    if unknown:
        raise ValueError(f"Unknown module ID: {sorted(unknown)[0]}")
    selected = tuple(module_id for module_id in MODULE_IDS if module_id in modules_raw)
    declined = tuple(module_id for module_id in MODULE_IDS if module_id in reasons and module_id not in selected)
    return Profile(1, __version__, answers, selected, declined, reasons)


def _plan_data(plan: InstallationPlan) -> dict[str, Any]:
    counts = {status.value: 0 for status in FileStatus}
    files: list[dict[str, str]] = []
    for item in plan.files:
        counts[item.status.value] += 1
        diff = ""
        if item.status in (FileStatus.MODIFIED, FileStatus.CONFLICT):
            destination = plan.target.joinpath(*item.relative_path.parts)
            diff = unified_diff(item, destination)
        files.append(
            {
                "path": item.relative_path.as_posix(),
                "status": item.status.value,
                "checksum": item.checksum,
                "diff": diff,
            }
        )
    return {
        "target": str(plan.target),
        "counts": counts,
        "files": files,
        "manual_integrations": list(plan.manual_integrations),
    }


def plan_payload(plan: InstallationPlan) -> dict[str, Any]:
    data = _plan_data(plan)
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    data["digest"] = hashlib.sha256(encoded).hexdigest()
    return data


def _config_payload(session: WebSetupSession) -> dict[str, Any]:
    profiles = {
        profile_id: {"modules": list(module_ids)}
        for profile_id, module_ids in SETUP_PROFILES.items()
    }
    if session.previous is not None:
        profiles["existing"] = {"modules": list(session.previous.selected_modules)}
    previous = None
    if session.previous is not None:
        previous = {
            "answers": dict(session.previous.answers),
            "selected_modules": list(session.previous.selected_modules),
        }
    return {
        "target": str(session.target.resolve(strict=False)),
        "profiles": profiles,
        "questions": [
            {
                "id": question.id,
                "prompt": question.prompt,
                "reason": question.reason,
                "recommends": list(question.recommends),
            }
            for question in QUESTIONS
        ],
        "modules": {
            module_id: {
                "title": MODULE_INFO[module_id].title,
                "recommended_when": MODULE_INFO[module_id].recommended_when,
                "covers": MODULE_INFO[module_id].covers,
                "generated": list(MODULE_INFO[module_id].generated),
            }
            for module_id in MODULE_IDS
        },
        "previous": previous,
    }


class _LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address: tuple[str, int], session: WebSetupSession) -> None:
        self.session = session
        super().__init__(address, _WebSetupHandler)


class _WebSetupHandler(BaseHTTPRequestHandler):
    server: _LocalServer

    def log_message(self, format: str, *args: object) -> None:
        return

    def _security_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            _security_policy(self.server.session.csp_nonce),
        )
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")

    def _send(self, status: int, content_type: str, content: bytes) -> None:
        self.send_response(status)
        self._security_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _json(self, status: int, data: object) -> None:
        content = json.dumps(data, separators=(",", ":")).encode("utf-8")
        self._send(status, "application/json; charset=utf-8", content)

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"error": message})

    def _expected_host(self) -> str:
        return f"127.0.0.1:{self.server.server_address[1]}"

    def _authorized(self, require_origin: bool) -> bool:
        if self.headers.get("Host") != self._expected_host():
            self._error(403, "Request host is not allowed")
            return False
        if require_origin:
            expected = f"http://{self._expected_host()}"
            if self.headers.get("Origin") != expected:
                self._error(403, "Request origin is not allowed")
                return False
        return True

    def _route(self) -> str | None:
        prefix = f"/{self.server.session.token}/"
        if not self.path.startswith(prefix) or "?" in self.path:
            return None
        return self.path[len(prefix) :]

    def _read_json(self) -> object | None:
        if self.headers.get_content_type() != "application/json":
            self._error(415, "Expected application/json")
            return None
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length or "")
        except ValueError:
            self._error(400, "Invalid Content-Length")
            return None
        if length < 0:
            self._error(400, "Invalid Content-Length")
            return None
        if length > MAX_REQUEST_BYTES:
            self._error(413, "Request body is too large")
            return None
        try:
            body: object = json.loads(self.rfile.read(length))
            return body
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._error(400, "Invalid JSON")
            return None

    def do_GET(self) -> None:
        if not self._authorized(require_origin=False):
            return
        route = self._route()
        if route == "":
            asset = Path(__file__).with_name("web") / "index.html"
            try:
                content = asset.read_text(encoding="utf-8").replace(
                    "__CSP_NONCE__",
                    self.server.session.csp_nonce,
                ).encode("utf-8")
            except OSError:
                self._error(500, "Web interface is unavailable")
                return
            self._send(200, "text/html; charset=utf-8", content)
        elif route == "api/config":
            self._json(200, _config_payload(self.server.session))
        else:
            self._error(404, "Not found")

    def do_POST(self) -> None:
        if not self._authorized(require_origin=True):
            return
        route = self._route()
        if route not in {"api/plan", "api/confirm", "api/cancel"}:
            self._error(404, "Not found")
            return
        body = self._read_json()
        if body is None:
            return
        try:
            if route == "api/plan":
                self._json(200, plan_payload(self.server.session.build_plan(body)))
                return
            if route == "api/cancel":
                self.server.session.cancelled = True
                self._json(200, {"cancelled": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return

            data = _require_dict(body, "confirmation")
            if set(data) != {"profile", "digest", "approved_paths"}:
                raise ValueError("Invalid confirmation fields")
            plan = self.server.session.build_plan(data["profile"])
            current = plan_payload(plan)
            if data["digest"] != current["digest"]:
                self._error(409, "The project changed; review a fresh plan")
                return
            approved_raw = data["approved_paths"]
            if not isinstance(approved_raw, list) or any(
                not isinstance(path, str) for path in approved_raw
            ):
                raise ValueError("approved_paths must be a list")
            approved = frozenset(approved_raw)
            required = {
                item.relative_path.as_posix()
                for item in plan.files
                if item.status in (FileStatus.MODIFIED, FileStatus.CONFLICT)
            }
            if approved != required:
                self._error(409, "Every changed or conflicting file must be approved")
                return
            self.server.session.result = WebSetupResult(
                plan.profile,
                approved,
                str(current["digest"]),
            )
            self._json(200, {"confirmed": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        except ValueError as error:
            self._error(400, str(error))


def create_web_server(session: WebSetupSession) -> _LocalServer:
    return _LocalServer(("127.0.0.1", 0), session)


def open_local_browser(
    url: str,
    *,
    platform: str = sys.platform,
    executable: str | None = None,
    wsl: bool | None = None,
    wsl_cmd_executable: str | None = None,
    wsl_executable: str | None = None,
    runner: Any = subprocess.run,
) -> bool:
    if platform.startswith("linux"):
        if wsl is None:
            wsl = bool(os.environ.get("WSL_DISTRO_NAME"))
            if not wsl:
                try:
                    release = Path("/proc/sys/kernel/osrelease").read_text(encoding="utf-8")
                except OSError:
                    release = ""
                wsl = "microsoft" in release.lower()
        commands: list[list[str]] = []
        if wsl:
            windows_shell = wsl_cmd_executable or shutil.which("cmd.exe")
            if windows_shell is not None:
                commands.append([windows_shell, "/d", "/c", "start", "", url])
            windows_browser = wsl_executable or shutil.which("explorer.exe")
            if windows_browser is not None:
                commands.append([windows_browser, url])
        linux_browser = executable or shutil.which("xdg-open")
        if linux_browser is not None:
            commands.append([linux_browser, url])
        for command in commands:
            try:
                completed = runner(
                    command,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            if completed.returncode == 0:
                return True
        return False
    try:
        return bool(webbrowser.open(url, new=2))
    except webbrowser.Error:
        return False


def run_web_setup(
    target: Path,
    template_root: Path,
    known_checksums: Mapping[str, str],
    previous: Profile | None = None,
    *,
    open_browser: bool = True,
    output_fn: Any = print,
    known_manual_integrations: Sequence[str] = (),
) -> WebSetupResult:
    session = WebSetupSession(
        target,
        template_root,
        known_checksums,
        previous,
        known_manual_integrations,
    )
    server = create_web_server(session)
    url = f"http://127.0.0.1:{server.server_address[1]}/{session.token}/"
    output_fn(f"Applied AI Rig setup: {url}")
    output_fn("The local server will stop after confirmation or cancellation.")
    if open_browser and not open_local_browser(url):
        output_fn("No browser could be opened automatically. Open the URL above manually.")
    try:
        server.serve_forever()
    except KeyboardInterrupt as error:
        raise WebSetupCancelled("Setup cancelled; no files were changed.") from error
    finally:
        server.server_close()
    if session.cancelled or session.result is None:
        raise WebSetupCancelled("Setup cancelled; no files were changed.")
    return session.result
