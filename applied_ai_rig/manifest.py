import json
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

from .intake import MODULE_IDS


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _require_modules(module_ids: tuple[str, ...]) -> None:
    unknown = set(module_ids) - set(MODULE_IDS)
    if unknown:
        raise ValueError(f"Unknown module ID: {sorted(unknown)[0]}")


def _require_relative_path(raw: str) -> None:
    path = PurePosixPath(raw)
    if (
        not raw
        or path.is_absolute()
        or PureWindowsPath(raw).is_absolute()
        or ".." in path.parts
        or "\\" in raw
    ):
        raise ValueError(f"Expected a relative project path: {raw}")


@dataclass(frozen=True)
class Profile:
    schema_version: int
    rig_version: str
    answers: dict[str, bool]
    selected_modules: tuple[str, ...]
    declined_modules: tuple[str, ...]
    recommendation_reasons: dict[str, str]

    def __post_init__(self) -> None:
        _require_modules(self.selected_modules)
        _require_modules(self.declined_modules)

    def to_json(self) -> str:
        return _json(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> "Profile":
        try:
            data = json.loads(raw)
            return cls(
                schema_version=int(data["schema_version"]),
                rig_version=str(data["rig_version"]),
                answers=dict(data["answers"]),
                selected_modules=tuple(data["selected_modules"]),
                declined_modules=tuple(data["declined_modules"]),
                recommendation_reasons=dict(data["recommendation_reasons"]),
            )
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid profile: {error}") from error


@dataclass(frozen=True)
class GeneratedFile:
    path: str
    original_checksum: str

    def __post_init__(self) -> None:
        _require_relative_path(self.path)
        if len(self.original_checksum) != 64 or any(
            char not in "0123456789abcdef" for char in self.original_checksum
        ):
            raise ValueError("Expected a lowercase SHA-256 checksum")


@dataclass(frozen=True)
class Manifest:
    schema_version: int
    rig_version: str
    installed_at: str
    selected_modules: tuple[str, ...]
    files: tuple[GeneratedFile, ...]
    manual_integrations: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_modules(self.selected_modules)
        for path in self.manual_integrations:
            _require_relative_path(path)

    def to_json(self) -> str:
        return _json(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> "Manifest":
        try:
            data = json.loads(raw)
            return cls(
                schema_version=int(data["schema_version"]),
                rig_version=str(data["rig_version"]),
                installed_at=str(data["installed_at"]),
                selected_modules=tuple(data["selected_modules"]),
                files=tuple(GeneratedFile(**item) for item in data["files"]),
                manual_integrations=tuple(data["manual_integrations"]),
            )
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid manifest: {error}") from error
