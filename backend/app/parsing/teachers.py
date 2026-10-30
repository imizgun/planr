"""Parsing of the 'nauczyciel' column (several teachers are joined with '+')."""


def split_teachers(value: str) -> list[str]:
    """'dr A+dr B' -> ['dr A', 'dr B'] (order preserved, duplicates and blanks removed)."""
    names: list[str] = []
    for part in value.split("+"):
        name = part.strip()
        if name and name not in names:
            names.append(name)
    return names
