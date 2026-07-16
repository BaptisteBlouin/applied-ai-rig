#!/usr/bin/env python3
"""Inspect built distributions and smoke-test the installed wheel."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Sequence

from packaging.requirements import InvalidRequirement, Requirement


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "applied_ai_rig"
OPTIONAL_EXTRA_MARKER = re.compile(r'extra == "[A-Za-z0-9][A-Za-z0-9._-]*"\Z')
REQUIRED_WHEEL_PATHS = tuple(
    sorted(
        path.relative_to(ROOT).as_posix()
        for path in PACKAGE_ROOT.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )
)
REQUIRED_SOURCE_PATHS = (
    "LICENSE",
    "MANIFEST.in",
    "README.md",
    "pyproject.toml",
    *REQUIRED_WHEEL_PATHS,
    "schemas/manifest.schema.json",
    "schemas/profile.schema.json",
)


class VerificationError(RuntimeError):
    """Raised when a distribution or installed-package smoke test is invalid."""


def _single_match(directory: Path, pattern: str, label: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if len(matches) != 1:
        names = ", ".join(path.name for path in matches) or "none"
        raise VerificationError(f"Expected exactly one {label}; found: {names}")
    return matches[0]


def _require_paths(names: set[str], required: Sequence[str], label: str) -> None:
    missing = [path for path in required if path not in names]
    if missing:
        raise VerificationError(f"{label} is missing: {', '.join(missing)}")


def _inspect_wheel(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        _require_paths(names, REQUIRED_WHEEL_PATHS, "wheel")

        metadata_paths = sorted(
            name for name in names if name.endswith(".dist-info/METADATA")
        )
        entry_point_paths = sorted(
            name for name in names if name.endswith(".dist-info/entry_points.txt")
        )
        if len(metadata_paths) != 1 or len(entry_point_paths) != 1:
            raise VerificationError(
                "wheel must contain exactly one METADATA file and one entry_points.txt"
            )

        metadata = BytesParser(policy=policy.default).parsebytes(
            archive.read(metadata_paths[0])
        )
        if metadata.get("Name") != "applied-ai-rig":
            raise VerificationError("wheel metadata has the wrong project name")
        runtime_dependencies: list[str] = []
        for raw_requirement in metadata.get_all("Requires-Dist", []):
            try:
                requirement = Requirement(raw_requirement)
            except InvalidRequirement as error:
                raise VerificationError(
                    f"wheel contains an invalid dependency declaration: {raw_requirement}"
                ) from error
            marker = str(requirement.marker) if requirement.marker is not None else ""
            if not OPTIONAL_EXTRA_MARKER.fullmatch(marker):
                runtime_dependencies.append(raw_requirement)
        if runtime_dependencies:
            raise VerificationError(
                "wheel declares a runtime dependency: "
                + ", ".join(runtime_dependencies)
            )

        entry_points = archive.read(entry_point_paths[0]).decode("utf-8")
        expected = "applied-ai-rig = applied_ai_rig.cli:main"
        if expected not in entry_points:
            raise VerificationError(f"wheel console entry point is missing: {expected}")


def _inspect_source(source: Path) -> None:
    with tarfile.open(source, "r:gz") as archive:
        names: set[str] = set()
        for member in archive.getmembers():
            parts = Path(member.name).parts
            if len(parts) > 1:
                names.add(Path(*parts[1:]).as_posix())
        _require_paths(names, REQUIRED_SOURCE_PATHS, "source distribution")


def inspect_distributions(dist_directory: Path) -> tuple[Path, Path]:
    """Return the sole wheel and sdist after checking their release contents."""
    if not dist_directory.is_dir():
        raise VerificationError(f"Distribution directory does not exist: {dist_directory}")
    wheel = _single_match(dist_directory, "*.whl", "wheel")
    source = _single_match(dist_directory, "*.tar.gz", "source distribution")
    _inspect_wheel(wheel)
    _inspect_source(source)
    return wheel, source


def _run(command: Sequence[str]) -> str:
    print(f"$ {shlex.join(command)}", flush=True)
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise VerificationError(
            f"Command exited with {result.returncode}: {shlex.join(command)}"
        )
    return result.stdout


def smoke_test_wheel(wheel: Path) -> None:
    """Install the wheel alone, then exercise the supported CLI workflow."""
    with tempfile.TemporaryDirectory(prefix="applied-ai-rig-package-") as directory:
        root = Path(directory)
        environment = root / "venv"
        target = root / "project with spaces"
        venv.EnvBuilder(with_pip=True).create(environment)
        if os.name == "nt":
            python = environment / "Scripts/python.exe"
            cli = environment / "Scripts/applied-ai-rig.exe"
        else:
            python = environment / "bin/python"
            cli = environment / "bin/applied-ai-rig"

        _run((str(python), "-m", "pip", "install", "--no-deps", str(wheel)))
        _run(
            (
                str(cli),
                str(target),
                "--modules",
                "evaluation",
                "--non-interactive",
            )
        )
        _run((str(cli), "status", str(target)))
        _run(
            (
                str(cli),
                "add",
                "decision",
                str(target),
                "--id",
                "DEC-CI-001",
                "--title",
                "Verify the installed package",
                "--yes",
            )
        )
        _run(
            (
                str(cli),
                "add",
                "evidence",
                str(target),
                "--id",
                "EVD-CI-001",
                "--claim",
                "The installed CLI completes its workflow",
                "--decision",
                "DEC-CI-001",
                "--status",
                "measured",
                "--yes",
            )
        )
        _run(
            (
                str(cli),
                "add",
                "experiment",
                str(target),
                "--run-id",
                "RUN-CI-001",
                "--decision",
                "DEC-CI-001",
                "--model",
                "fixture-model",
                "--metric",
                "success",
                "--value",
                "1",
                "--yes",
            )
        )
        _run((str(cli), str(target), "--check"))

        expected_files = (
            target / ".applied-ai-rig/manifest.json",
            target / "docs/applied-ai-rig/DECISIONS.md",
            target / "docs/applied-ai-rig/EVIDENCE.md",
            target / "docs/applied-ai-rig/modules/evaluation/experiments.csv",
        )
        missing = [str(path.relative_to(target)) for path in expected_files if not path.is_file()]
        if missing:
            raise VerificationError(
                "installed CLI smoke test did not create: " + ", ".join(missing)
            )


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv) if argv is not None else sys.argv[1:]
    if len(arguments) != 1:
        print("Usage: python tools/verify_package.py DIST_DIRECTORY", file=sys.stderr)
        return 2
    try:
        wheel, source = inspect_distributions(Path(arguments[0]))
        print(f"Verified wheel contents: {wheel.name}")
        print(f"Verified source contents: {source.name}")
        smoke_test_wheel(wheel.resolve())
    except (OSError, VerificationError, tarfile.TarError, zipfile.BadZipFile) as error:
        print(f"Package verification failed: {error}", file=sys.stderr)
        return 1
    print("Installed-package smoke test completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
