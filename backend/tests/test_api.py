from sqlalchemy import select

from app.ids import course_public_id, group_public_id
from app.models import Course, Group


def _program(catalog, program_id):
    return next(p for p in catalog["programs"] if p["id"] == program_id)


def test_catalog_requires_data(client):
    assert client.get("/api/v1/catalog").status_code == 503
    assert client.get("/api/v1/schedule", params={"program": "x"}).status_code == 503


def test_catalog_shape(client, loaded):
    body = client.get("/api/v1/catalog").json()
    assert body["schema_version"] == 1
    assert body["source"]["version"] == loaded.version
    assert body["source"]["fetched_at"].endswith("Z")
    program = _program(body, "informatyka-p-2")
    assert program["name"] == "informatyka (P): II rok"
    assert [g["label"] for g in program["groups"]] == ["gr. 1", "gr. 2", "gr. 3", "gr. 4"]
    assert program["electives"] == []  # assignment chain not implemented yet


def test_schedule_selects_requested_group_and_program_wide_items(client, loaded):
    catalog = client.get("/api/v1/catalog").json()
    gr1 = next(g["id"] for g in _program(catalog, "informatyka-p-2")["groups"] if g["label"] == "gr. 1")
    body = client.get("/api/v1/schedule", params={"program": "informatyka-p-2", "group": gr1}).json()
    assert body["program"] == {"id": "informatyka-p-2", "name": "informatyka (P): II rok"}
    assert body["source"]["timezone"] == "Europe/Warsaw"
    labels = {(i["group"]["label"], i["group"]["program_wide"]) for i in body["items"]}
    assert labels == {("gr. 1", False), (None, True)}
    assert all(i["proposals"] == [] for i in body["items"])
    keys = [(i["effective"]["weekday"], i["effective"]["start_time"]) for i in body["items"]]
    assert keys == sorted(keys)


def test_item_matches_any_group_of_a_multi_group_row(client, loaded):
    catalog = client.get("/api/v1/catalog").json()
    gr4 = next(g["id"] for g in _program(catalog, "informatyka-p-2")["groups"] if g["label"] == "gr. 4")
    items = client.get("/api/v1/schedule", params={"program": "informatyka-p-2", "group": gr4}).json()["items"]
    shared = [i for i in items if i["remark"]["raw"] == "grupy na zmianę co 2 tygodnie"]
    assert shared and shared[0]["group"]["label"] == "gr. 4"


def test_remark_patch_is_reflected(client, loaded):
    items = client.get("/api/v1/schedule", params={"program": "informatyka-p-2"}).json()["items"]
    remote = next(i for i in items if i["remark"]["raw"] == "dokładne terminy zostaną podane później; zajęcia zdalne")
    assert remote["effective"]["mode"] == "remote" and remote["patched_fields"] == ["mode"]
    assert remote["remark"] == {
        "raw": remote["remark"]["raw"], "parse_status": "partial",
        "unparsed": "dokładne terminy zostaną podane później", "needs_review": True,
    }


def test_elective_selection(client, session, loaded):
    course = session.scalar(select(Course).where(Course.name == "Programowanie funkcyjne"))
    groups = {g.label: g for g in session.scalars(select(Group).where(Group.course_id == course.id))}
    assert set(groups) == {"gr. 1", "gr. 2"}
    selector = f"{course_public_id(course.id)}:{group_public_id(groups['gr. 1'].id, course.id)}"
    items = client.get("/api/v1/schedule", params={"program": "informatyka-p-2", "elective": selector}).json()["items"]
    elective = [i for i in items if i["course"]["name"] == "Programowanie funkcyjne"]
    assert {(i["type"], (i["group"] or {}).get("label")) for i in elective} == {("wykład", None), ("laboratorium", "gr. 1")}


def test_date_filter(client, loaded):
    params = {"program": "informatyka-p-2"}
    everything = client.get("/api/v1/schedule", params=params).json()["items"]
    december = client.get("/api/v1/schedule", params={**params, "from": "2026-12-15", "to": "2026-12-20"}).json()["items"]
    assert 0 < len(december) < len(everything)
    assert all((i["effective"]["date_to"] or "9999") >= "2026-12-15" for i in december)


def test_invalid_requests(client, loaded):
    assert client.get("/api/v1/schedule", params={"program": "nope"}).status_code == 404
    assert client.get("/api/v1/schedule", params={"program": "informatyka-p-2", "group": "grp_99999"}).status_code == 422
    assert client.get("/api/v1/schedule", params={"program": "informatyka-p-2", "group": "abc"}).status_code == 422
    assert client.get("/api/v1/schedule", params={"program": "informatyka-p-2", "elective": "crs_1"}).status_code == 422
    assert client.get(
        "/api/v1/schedule", params={"program": "informatyka-p-2", "from": "2027-02-01", "to": "2027-01-01"}
    ).status_code == 422
    assert client.get("/api/v1/schedule").status_code == 422


def test_bare_course_id_only_for_courses_without_groups(client, session, loaded):
    with_groups = session.scalar(select(Course).where(Course.name == "Programowanie funkcyjne"))
    without = session.scalar(select(Course).where(Course.name == "Podstawy kryptografii"))
    assert not session.scalar(select(Group).where(Group.course_id == without.id))
    params = {"program": "informatyka-p-2"}
    rejected = client.get("/api/v1/schedule", params={**params, "elective": course_public_id(with_groups.id)})
    assert rejected.status_code == 422
    accepted = client.get("/api/v1/schedule", params={**params, "elective": course_public_id(without.id)})
    assert accepted.status_code == 200
    assert {i["course"]["name"] for i in accepted.json()["items"] if i["group"] is None} >= {"Podstawy kryptografii"}
