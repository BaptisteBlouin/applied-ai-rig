import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from subprocess import CompletedProcess, DEVNULL
from unittest.mock import Mock

from applied_ai_rig.installer import FileStatus, build_plan
from applied_ai_rig.manifest import Profile
from applied_ai_rig.web_setup import (
    WebSetupSession,
    open_local_browser,
    create_web_server,
    plan_payload,
    profile_from_web_payload,
)


ROOT = Path(__file__).resolve().parents[1]


class WebProfileTests(unittest.TestCase):
    def test_quick_profile_does_not_accept_factual_answers(self) -> None:
        with self.assertRaisesRegex(ValueError, "answers"):
            profile_from_web_payload(
                {
                    "route": "api-rag",
                    "answers": {"external_model_api": True},
                    "selected_modules": ["model-api", "data", "evaluation"],
                }
            )

    def test_custom_assessment_records_reasons_and_declined_modules(self) -> None:
        profile = profile_from_web_payload(
            {
                "route": "custom",
                "answers": {
                    "external_model_api": True,
                    "sensitive_or_supplied_data": False,
                    "persist_model_content": False,
                    "quality_claims": True,
                    "side_effects": False,
                    "production_use": False,
                },
                "selected_modules": ["evaluation"],
            }
        )

        self.assertEqual(profile.selected_modules, ("evaluation",))
        self.assertEqual(profile.declined_modules, ("model-api",))
        self.assertIn("model-api", profile.recommendation_reasons)
        self.assertIn("evaluation", profile.recommendation_reasons)

    def test_unknown_and_duplicate_modules_are_rejected(self) -> None:
        for modules in (["future-module"], ["data", "data"]):
            with self.subTest(modules=modules):
                with self.assertRaisesRegex(ValueError, "module"):
                    profile_from_web_payload(
                        {"route": "minimal", "answers": {}, "selected_modules": modules}
                    )

    def test_existing_route_preserves_answers_and_recommendation_reasons(self) -> None:
        previous = Profile(
            1,
            "0.1.0",
            {"external_model_api": True},
            ("model-api",),
            (),
            {"model-api": "Existing reason."},
        )

        profile = profile_from_web_payload(
            {"route": "existing", "answers": {}, "selected_modules": ["data"]},
            previous,
        )

        self.assertEqual(dict(profile.answers), {"external_model_api": True})
        self.assertEqual(profile.selected_modules, ("data",))
        self.assertEqual(profile.declined_modules, ("model-api",))
        self.assertEqual(profile.recommendation_reasons["model-api"], "Existing reason.")


class BrowserLaunchTests(unittest.TestCase):
    def test_wsl_prefers_windows_url_handler_over_xdg_open(self) -> None:
        runner = Mock(return_value=CompletedProcess(["cmd.exe"], 0))

        opened = open_local_browser(
            "http://127.0.0.1:1234/session/",
            platform="linux",
            executable="/usr/bin/xdg-open",
            wsl=True,
            wsl_cmd_executable="/mnt/c/Windows/System32/cmd.exe",
            wsl_executable="/mnt/c/Windows/explorer.exe",
            runner=runner,
        )

        self.assertTrue(opened)
        runner.assert_called_once_with(
            [
                "/mnt/c/Windows/System32/cmd.exe",
                "/d",
                "/c",
                "start",
                "",
                "http://127.0.0.1:1234/session/",
            ],
            check=False,
            stdout=DEVNULL,
            stderr=DEVNULL,
            timeout=5,
        )

    def test_linux_browser_failure_is_silent_and_reported(self) -> None:
        runner = Mock(return_value=CompletedProcess(["xdg-open"], 3))

        opened = open_local_browser(
            "http://127.0.0.1:1234/session/",
            platform="linux",
            executable="/usr/bin/xdg-open",
            wsl=False,
            runner=runner,
        )

        self.assertFalse(opened)
        runner.assert_called_once_with(
            ["/usr/bin/xdg-open", "http://127.0.0.1:1234/session/"],
            check=False,
            stdout=DEVNULL,
            stderr=DEVNULL,
            timeout=5,
        )


class WebPlanTests(unittest.TestCase):
    def test_plan_payload_contains_real_statuses_diffs_and_digest(self) -> None:
        profile = profile_from_web_payload(
            {"route": "minimal", "answers": {}, "selected_modules": []}
        )
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            conflict = target / "APPLIED_AI_RIG_AGENT.md"
            conflict.write_text("project-owned instructions\n", encoding="utf-8")
            plan = build_plan(target, profile, ROOT / "applied_ai_rig" / "templates")

            payload = plan_payload(plan)

        item = next(
            item for item in payload["files"] if item["path"] == "APPLIED_AI_RIG_AGENT.md"
        )
        self.assertEqual(item["status"], FileStatus.CONFLICT.value)
        self.assertIn("project-owned instructions", item["diff"])
        self.assertEqual(len(payload["digest"]), 64)
        self.assertEqual(payload["counts"][FileStatus.CONFLICT.value], 1)


class LocalWebServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.target = Path(self.temp.name)
        self.session = WebSetupSession(self.target, ROOT / "applied_ai_rig" / "templates", {})
        self.server = create_web_server(self.session)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def request(
        self,
        method: str,
        suffix: str,
        body: dict[str, object] | None = None,
        *,
        host: str | None = None,
        origin: str | None = None,
    ) -> http.client.HTTPResponse:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        headers = {"Host": host or f"127.0.0.1:{self.port}"}
        raw = None
        if body is not None:
            raw = json.dumps(body)
            headers["Content-Type"] = "application/json"
            headers["Origin"] = origin or f"http://127.0.0.1:{self.port}"
        connection.request(method, f"/{self.session.token}/{suffix}", raw, headers)
        response = connection.getresponse()
        response.body = response.read()  # type: ignore[attr-defined]
        connection.close()
        return response

    def test_page_has_restrictive_security_headers(self) -> None:
        response = self.request("GET", "")

        self.assertEqual(response.status, 200)
        policy = response.getheader("Content-Security-Policy")
        self.assertIn("default-src 'none'", policy)
        self.assertIn("script-src 'nonce-", policy)
        self.assertNotIn("unsafe-inline", policy)
        self.assertIn(
            f'nonce="{self.session.csp_nonce}"'.encode(),
            response.body,  # type: ignore[attr-defined]
        )
        self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.getheader("Cache-Control"), "no-store")

    def test_wrong_host_and_cross_origin_posts_are_rejected(self) -> None:
        wrong_host = self.request("GET", "", host="attacker.example")
        wrong_origin = self.request(
            "POST",
            "api/plan",
            {"route": "minimal", "answers": {}, "selected_modules": []},
            origin="https://attacker.example",
        )

        self.assertEqual(wrong_host.status, 403)
        self.assertEqual(wrong_origin.status, 403)

    def test_invalid_json_and_oversized_requests_are_rejected(self) -> None:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        headers = {
            "Host": f"127.0.0.1:{self.port}",
            "Origin": f"http://127.0.0.1:{self.port}",
            "Content-Type": "application/json",
        }
        connection.request("POST", f"/{self.session.token}/api/plan", "not-json", headers)
        invalid = connection.getresponse()
        invalid.read()
        connection.close()

        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        oversized_headers = dict(headers, **{"Content-Length": "70000"})
        connection.request(
            "POST",
            f"/{self.session.token}/api/plan",
            body=b"{}",
            headers=oversized_headers,
            encode_chunked=False,
        )
        oversized = connection.getresponse()
        oversized.read()
        connection.close()

        self.assertEqual(invalid.status, 400)
        self.assertEqual(oversized.status, 413)

    def test_confirmation_requires_current_digest_and_all_conflicts(self) -> None:
        (self.target / "APPLIED_AI_RIG_AGENT.md").write_text(
            "project-owned instructions\n", encoding="utf-8"
        )
        profile = {"route": "minimal", "answers": {}, "selected_modules": []}
        preview = self.request("POST", "api/plan", profile)
        plan_data = json.loads(preview.body)  # type: ignore[attr-defined]

        missing_approval = self.request(
            "POST",
            "api/confirm",
            {"profile": profile, "digest": plan_data["digest"], "approved_paths": []},
        )
        stale = self.request(
            "POST",
            "api/confirm",
            {
                "profile": profile,
                "digest": "0" * 64,
                "approved_paths": ["APPLIED_AI_RIG_AGENT.md"],
            },
        )

        self.assertEqual(missing_approval.status, 409)
        self.assertEqual(stale.status, 409)
        self.assertIsNone(self.session.result)

    def test_successful_confirmation_returns_validated_profile_and_approvals(self) -> None:
        (self.target / "APPLIED_AI_RIG_AGENT.md").write_text(
            "project-owned instructions\n", encoding="utf-8"
        )
        profile = {"route": "minimal", "answers": {}, "selected_modules": []}
        preview = self.request("POST", "api/plan", profile)
        plan_data = json.loads(preview.body)  # type: ignore[attr-defined]

        confirmed = self.request(
            "POST",
            "api/confirm",
            {
                "profile": profile,
                "digest": plan_data["digest"],
                "approved_paths": ["APPLIED_AI_RIG_AGENT.md"],
            },
        )

        self.assertEqual(confirmed.status, 200)
        self.assertIsNotNone(self.session.result)
        self.assertEqual(self.session.result.profile.selected_modules, ())
        self.assertEqual(
            self.session.result.approved_paths,
            frozenset({"APPLIED_AI_RIG_AGENT.md"}),
        )


if __name__ == "__main__":
    unittest.main()
