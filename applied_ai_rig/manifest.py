import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Any

from .intake import MODULE_IDS


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _require_modules(module_ids: tuple[str, ...]) -> None:
    unknown = set(module_ids) - set(MODULE_IDS)
    if unknown:
        raise ValueError(f"Unknown module ID: {sorted(unknown)[0]}")
    if len(module_ids) != len(set(module_ids)):
        raise ValueError("Module IDs must be unique")


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
    answers: Mapping[str, bool]
    selected_modules: tuple[str, ...]
    declined_modules: tuple[str, ...]
    recommendation_reasons: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "answers", MappingProxyType(dict(self.answers)))
        object.__setattr__(
            self,
            "recommendation_reasons",
            MappingProxyType(dict(self.recommendation_reasons)),
        )
        if self.schema_version != 1:
            raise ValueError(f"Unsupported profile schema version: {self.schema_version}")
        if not self.rig_version:
            raise ValueError("Rig version must not be empty")
        _require_modules(self.selected_modules)
        _require_modules(self.declined_modules)
        if set(self.selected_modules) & set(self.declined_modules):
            raise ValueError("A module cannot be both selected and declined")
        if any(not isinstance(value, bool) for value in self.answers.values()):
            raise ValueError("Profile answers must be booleans")
        _require_modules(tuple(self.recommendation_reasons))

    def to_json(self) -> str:
        return _json(
            {
                "schema_version": self.schema_version,
                "rig_version": self.rig_version,
                "answers": dict(self.answers),
                "selected_modules": self.selected_modules,
                "declined_modules": self.declined_modules,
                "recommendation_reasons": dict(self.recommendation_reasons),
            }
        )

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
    manual_integration_statuses: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        statuses = dict(self.manual_integration_statuses)
        if self.manual_integrations and not statuses:
            statuses = {path: "proposed" for path in self.manual_integrations}
        object.__setattr__(
            self,
            "manual_integration_statuses",
            MappingProxyType(statuses),
        )
        if self.schema_version != 1:
            raise ValueError(f"Unsupported manifest schema version: {self.schema_version}")
        if not self.rig_version:
            raise ValueError("Rig version must not be empty")
        _require_modules(self.selected_modules)
        paths = tuple(item.path for item in self.files)
        if len(paths) != len(set(paths)):
            raise ValueError("Manifest file paths must be unique")
        for path in self.manual_integrations:
            _require_relative_path(path)
        if set(self.manual_integration_statuses) != set(self.manual_integrations):
            raise ValueError("Manual integration statuses must match proposed paths")
        if any(
            status not in {"proposed", "accepted", "declined", "completed"}
            for status in self.manual_integration_statuses.values()
        ):
            raise ValueError("Unknown manual integration status")

    def to_json(self) -> str:
        return _json(
            {
                "schema_version": self.schema_version,
                "rig_version": self.rig_version,
                "installed_at": self.installed_at,
                "selected_modules": self.selected_modules,
                "files": [asdict(item) for item in self.files],
                "manual_integrations": self.manual_integrations,
                "manual_integration_statuses": dict(self.manual_integration_statuses),
            }
        )

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
                manual_integration_statuses=dict(
                    data.get(
                        "manual_integration_statuses",
                        {path: "proposed" for path in data["manual_integrations"]},
                    )
                ),
            )
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid manifest: {error}") from error
