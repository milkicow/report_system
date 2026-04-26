from datetime import date, timedelta


def _make_report(client, auth_headers, project_id, hours=6.0, days_ago=0):
    report_date = (date.today() - timedelta(days=days_ago)).isoformat()
    return client.post(
        "/reports/",
        json={
            "project_id": project_id,
            "report_date": report_date,
            "hours_spent": hours,
            "category": "dev",
        },
        headers=auth_headers,
    )


def test_create_report(client, test_project, auth_headers):
    resp = _make_report(client, auth_headers, test_project["id"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["hours_spent"] == 6.0
    assert data["category"] == "dev"


def test_create_report_requires_auth(client, test_project):
    resp = client.post(
        "/reports/",
        json={
            "project_id": test_project["id"],
            "report_date": date.today().isoformat(),
            "hours_spent": 5.0,
        },
    )
    assert resp.status_code == 401


def test_hours_zero_invalid(client, test_project, auth_headers):
    resp = _make_report(client, auth_headers, test_project["id"], hours=0.0)
    assert resp.status_code == 422


def test_hours_over_24_invalid(client, test_project, auth_headers):
    resp = _make_report(client, auth_headers, test_project["id"], hours=25.0)
    assert resp.status_code == 422


def test_get_report(client, test_project, auth_headers):
    report = _make_report(client, auth_headers, test_project["id"]).json()
    resp = client.get(f"/reports/{report['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == report["id"]


def test_get_report_not_found(client):
    assert client.get("/reports/9999").status_code == 404


def test_update_report(client, test_project, auth_headers):
    report = _make_report(client, auth_headers, test_project["id"]).json()
    resp = client.patch(
        f"/reports/{report['id']}",
        json={"hours_spent": 8.0, "comment": "Updated"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["hours_spent"] == 8.0


def test_delete_report(client, test_project, auth_headers):
    report = _make_report(client, auth_headers, test_project["id"]).json()
    resp = client.delete(f"/reports/{report['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get(f"/reports/{report['id']}").status_code == 404


def test_list_reports_filter_by_project(client, test_project, auth_headers):
    proj2 = client.post("/projects/", json={"name": "P2"}, headers=auth_headers).json()
    _make_report(client, auth_headers, test_project["id"])
    _make_report(client, auth_headers, proj2["id"])

    resp = client.get(f"/reports/?project_id={test_project['id']}")
    assert resp.status_code == 200
    assert all(r["project_id"] == test_project["id"] for r in resp.json())


def test_list_reports_filter_by_date(client, test_project, auth_headers):
    _make_report(client, auth_headers, test_project["id"], days_ago=0)
    _make_report(client, auth_headers, test_project["id"], days_ago=10)

    date_from = (date.today() - timedelta(days=5)).isoformat()
    resp = client.get(f"/reports/?date_from={date_from}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
