"""Parsing of the 'grupa' column, e.g. 'informatyka (P): II rok gr. 1/informatyka (P): II rok gr. 4'."""
import re
import unicodedata
from dataclasses import dataclass

_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
_ENTRY = re.compile(r"^(?P<program>.+?): (?P<year>[IVX]+) rok(?: (?P<label>.+))?$")
_NUMBERED_ENTRY = re.compile(r"^(?P<program>[^\d:]+?) \d+$")  # e.g. 'Biotech 3' = group 3 of 'Biotech'
_SEPARATOR = re.compile(r"\s*[/+]\s*")
_EXTRA_FOLD = str.maketrans({"ł": "l", "Ł": "L"})


@dataclass(frozen=True)
class GroupRef:
    program_id: str
    program_name: str
    label: str | None  # None = whole programme


def slugify(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.translate(_EXTRA_FOLD))
    ascii_text = folded.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")


def _parse_entry(entry: str) -> GroupRef:
    match = _ENTRY.match(entry)
    if match and match["year"] in _ROMAN:
        year = _ROMAN[match["year"]]
        return GroupRef(
            program_id=f"{slugify(match['program'])}-{year}",
            program_name=f"{match['program']}: {match['year']} rok",
            label=match["label"],
        )
    # Entries outside the '<programme>: <year> rok [<group>]' template (e.g. 'Biotech 2', 'OCEAN')
    numbered = _NUMBERED_ENTRY.match(entry)
    if numbered:
        program = numbered["program"]
        return GroupRef(program_id=slugify(program), program_name=program, label=entry)
    return GroupRef(program_id=slugify(entry), program_name=entry, label=None)


def parse_group_field(value: str) -> list[GroupRef]:
    """Split the raw column into distinct group references (order preserved)."""
    refs: list[GroupRef] = []
    for entry in filter(None, _SEPARATOR.split(value.strip())):
        ref = _parse_entry(entry)
        if ref not in refs:
            refs.append(ref)
    return refs
