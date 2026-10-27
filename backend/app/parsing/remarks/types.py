from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class AnalysisPart:
    """Information extracted from remark segments by one analysis stage.

    patch  - values overriding the 'effective' block of the schedule item (exposed by the API)
    extras - recognised information without a counterpart in the current API schema
    """

    patch: dict[str, Any] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)

    def conflicts_with(self, other: "AnalysisPart") -> bool:
        """True when 'other' sets an already-set key to a different value."""
        for mine, theirs in ((self.patch, other.patch), (self.extras, other.extras)):
            if any(key in mine and mine[key] != value for key, value in theirs.items()):
                return True
        return False

    def merge(self, other: "AnalysisPart") -> None:
        self.patch.update(other.patch)
        self.extras.update(other.extras)


class RemarkAnalyzer(Protocol):
    """One stage of the hierarchical analysis (regex -> LLM -> ...).

    Receives the segments left over by previous stages and returns what it recognised
    together with the segments it could not interpret.
    """

    name: str

    def analyze(self, segments: list[str]) -> tuple[AnalysisPart, list[str]]: ...


@dataclass
class RemarkResult:
    raw: str
    patch: dict[str, Any]
    extras: dict[str, Any]
    unparsed: list[str]
    stages: list[str]  # names of the stages that recognised something

    @property
    def recognized(self) -> bool:
        return bool(self.patch or self.extras)

    @property
    def parse_status(self) -> str:
        if not self.unparsed:
            return "ok"
        return "partial" if self.recognized else "unparsed"

    @property
    def needs_review(self) -> bool:
        return bool(self.unparsed)
