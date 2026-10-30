"""Hierarchical remark analysis: regex -> (LLM, not implemented yet) -> fallback (left unparsed)."""
from collections.abc import Sequence

from app.parsing.remarks.regex_rules import RegexAnalyzer
from app.parsing.remarks.types import AnalysisPart, RemarkAnalyzer, RemarkResult

DEFAULT_ANALYZERS: tuple[RemarkAnalyzer, ...] = (RegexAnalyzer(),)


def split_segments(raw: str) -> list[str]:
    return [segment.strip() for segment in raw.split(";") if segment.strip()]


def analyze_remark(raw: str, analyzers: Sequence[RemarkAnalyzer] = DEFAULT_ANALYZERS) -> RemarkResult:
    """Run the stages in order; each stage only sees what previous stages left over.

    Values recognised by an earlier stage take precedence over later stages.
    """
    merged = AnalysisPart()
    segments = split_segments(raw)
    stages: list[str] = []

    for analyzer in analyzers:
        if not segments:
            break
        part, segments = analyzer.analyze(segments)
        if part.patch or part.extras:
            stages.append(analyzer.name)
        for key, value in part.patch.items():
            merged.patch.setdefault(key, value)
        for key, value in part.extras.items():
            merged.extras.setdefault(key, value)

    return RemarkResult(raw=raw, patch=merged.patch, extras=merged.extras, unparsed=segments, stages=stages)
