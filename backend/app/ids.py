"""Public (API-facing) identifier formats. Internal integer keys are never exposed directly."""
import re

_COURSE = re.compile(r"^crs_(\d+)$")
_GROUP = re.compile(r"^grp_(?:e\d+_)?(\d+)$")


def course_public_id(course_id: int) -> str:
    return f"crs_{course_id}"


def teacher_public_id(teacher_id: int) -> str:
    return f"t_{teacher_id}"


def group_public_id(group_id: int, course_id: int | None) -> str:
    """Program groups: grp_<id>. Elective groups: grp_e<courseId>_<id>."""
    return f"grp_e{course_id}_{group_id}" if course_id is not None else f"grp_{group_id}"


def parse_course_id(value: str) -> int:
    match = _COURSE.match(value)
    if not match:
        raise ValueError(f"Malformed course id: {value!r}")
    return int(match.group(1))


def parse_group_id(value: str) -> int:
    match = _GROUP.match(value)
    if not match:
        raise ValueError(f"Malformed group id: {value!r}")
    return int(match.group(1))
