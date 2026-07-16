import importlib.util
import io
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "tools/verify_package.py"
PACKAGE_SOURCE_FILES = tuple(
    sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "applied_ai_rig").rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )
)

WHEEL_FILES = {
    **{name: b"fixture\n" for name in PACKAGE_SOURCE_FILES},
    "applied_ai_rig/__init__.py": b'__version__ = "0.2.0"\n',
    "applied_ai_rig/cli.py": b"def main(): return 0\n",
    "applied_ai_rig-0.2.0.dist-info/METADATA": (
        b"Metadata-Version: 2.4\n"
        b"Name: applied-ai-rig\n"
        b"Version: 0.2.0\n"
        b'Requires-Dist: ruff; extra == "dev"\n\n'
    ),
    "applied_ai_rig-0.2.0.dist-info/entry_points.txt": (
        b"[console_scripts]\napplied-ai-rig = applied_ai_rig.cli:main\n"
    ),
}


def load_verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_package", VERIFIER)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load packaging verifier: {VERIFIER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_distribution_pair(
    directory: Path,
    metadata: bytes | None = None,
    omitted_wheel_path: str | None = None,
    omitted_source_path: str | None = None,
) -> None:
    wheel_files = dict(WHEEL_FILES)
    if metadata is not None:
        wheel_files["applied_ai_rig-0.2.0.dist-info/METADATA"] = metadata
    if omitted_wheel_path is not None:
        wheel_files.pop(omitted_wheel_path)

    with zipfile.ZipFile(directory / "applied_ai_rig-0.2.0-py3-none-any.whl", "w") as archive:
        for name, content in wheel_files.items():
            archive.writestr(name, content)

    with tarfile.open(directory / "applied_ai_rig-0.2.0.tar.gz", "w:gz") as archive:
        for name in (
            "README.md",
            "LICENSE",
            "MANIFEST.in",
            "pyproject.toml",
            *PACKAGE_SOURCE_FILES,
            "schemas/manifest.schema.json",
            "schemas/profile.schema.json",
        ):
            if name == omitted_source_path:
                continue
            content = b"fixture\n"
            info = tarfile.TarInfo(f"applied_ai_rig-0.2.0/{name}")
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))


class PackagingCiTests(unittest.TestCase):
    def test_pyproject_uses_current_license_and_explicit_package_data_metadata(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('requires = ["setuptools>=77.0.3"]', pyproject)
        self.assertIn('requires-python = ">=3.10"', pyproject)
        self.assertIn('license = "MIT"', pyproject)
        self.assertIn('license-files = ["LICENSE"]', pyproject)
        self.assertIn("include-package-data = false", pyproject)

    def test_ci_builds_verifies_uploads_and_tests_the_local_action(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertIn('python -m pip install -e ".[dev]"', workflow)
        self.assertIn("package:", workflow)
        self.assertIn("python -m pip install -r requirements/release.txt", workflow)
        self.assertIn("python -m build --no-isolation", workflow)
        self.assertIn("python tools/verify_package.py dist", workflow)
        self.assertIn("uses: ./", workflow)
        self.assertIn("actions/upload-artifact@", workflow)
        self.assertIn("path: dist/", workflow)
        self.assertIn("ubuntu-latest", workflow)
        self.assertIn("macos-latest", workflow)
        self.assertIn("windows-latest", workflow)
        self.assertIn("applied-ai-rig-distributions-${{ matrix.os }}", workflow)

    def test_distribution_inspection_accepts_complete_dependency_free_archives(self) -> None:
        verifier = load_verifier()
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory)
            write_distribution_pair(dist)

            wheel, source = verifier.inspect_distributions(dist)

        self.assertEqual(wheel.name, "applied_ai_rig-0.2.0-py3-none-any.whl")
        self.assertEqual(source.name, "applied_ai_rig-0.2.0.tar.gz")

    def test_distribution_inspection_rejects_a_runtime_dependency(self) -> None:
        verifier = load_verifier()
        metadata = (
            b"Metadata-Version: 2.4\n"
            b"Name: applied-ai-rig\n"
            b"Version: 0.2.0\n"
            b"Requires-Dist: requests>=2\n\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory)
            write_distribution_pair(dist, metadata)

            with self.assertRaisesRegex(verifier.VerificationError, "runtime dependency"):
                verifier.inspect_distributions(dist)

    def test_distribution_inspection_rejects_conditional_runtime_dependency(self) -> None:
        verifier = load_verifier()
        metadata = (
            b"Metadata-Version: 2.4\n"
            b"Name: applied-ai-rig\n"
            b"Version: 0.2.0\n"
            b'Requires-Dist: requests; python_version < "3.11"\n\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory)
            write_distribution_pair(dist, metadata)

            with self.assertRaisesRegex(verifier.VerificationError, "runtime dependency"):
                verifier.inspect_distributions(dist)

    def test_distribution_inspection_requires_every_package_file_and_schema(self) -> None:
        verifier = load_verifier()
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory)
            write_distribution_pair(
                dist,
                omitted_wheel_path=(
                    "applied_ai_rig/templates/modules/operations/service_register.csv.tmpl"
                ),
            )
            with self.assertRaisesRegex(verifier.VerificationError, "wheel is missing"):
                verifier.inspect_distributions(dist)

        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory)
            write_distribution_pair(
                dist,
                omitted_source_path="schemas/profile.schema.json",
            )
            with self.assertRaisesRegex(
                verifier.VerificationError, "source distribution is missing"
            ):
                verifier.inspect_distributions(dist)


if __name__ == "__main__":
    unittest.main()
