import json
import unittest

from applied_ai_rig.manifest import GeneratedFile, Manifest, Profile


class ProfileTests(unittest.TestCase):
    def test_profile_round_trip_preserves_decisions_and_reasons(self) -> None:
        profile = Profile(
            schema_version=1,
            rig_version="0.1.0",
            answers={"external_model_api": True, "quality_claims": False},
            selected_modules=("model-api",),
            declined_modules=("evaluation",),
            recommendation_reasons={"model-api": "Track attributable usage."},
        )

        encoded = profile.to_json()
        decoded = Profile.from_json(encoded)

        self.assertEqual(decoded, profile)
        self.assertEqual(encoded, decoded.to_json())

    def test_profile_rejects_unknown_module(self) -> None:
        payload = {
            "schema_version": 1,
            "rig_version": "0.1.0",
            "answers": {},
            "selected_modules": ["future-module"],
            "declined_modules": [],
            "recommendation_reasons": {},
        }

        with self.assertRaisesRegex(ValueError, "Unknown module ID"):
            Profile.from_json(json.dumps(payload))


class ManifestTests(unittest.TestCase):
    def test_manifest_round_trip_preserves_generated_files(self) -> None:
        manifest = Manifest(
            schema_version=1,
            rig_version="0.1.0",
            installed_at="2026-07-15T10:00:00Z",
            selected_modules=("data",),
            files=(GeneratedFile("docs/applied-ai-rig/README.md", "a" * 64),),
            manual_integrations=("AGENTS.md",),
        )

        self.assertEqual(Manifest.from_json(manifest.to_json()), manifest)

    def test_manifest_rejects_absolute_and_parent_paths(self) -> None:
        for path in ("/tmp/secret", "C:/Users/example/secret", "../outside", "docs/../../outside"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, "relative project path"):
                    GeneratedFile(path, "a" * 64)

    def test_manifest_rejects_invalid_checksum(self) -> None:
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            GeneratedFile("README.md", "not-a-checksum")


if __name__ == "__main__":
    unittest.main()
