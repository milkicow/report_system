from datetime import date, datetime, timedelta, timezone

from app.models import Issue


def _create_issue(
    client, auth_headers, proj_id, title="Task", status="open", story_points=3
):
    resp = client.post(
        "/issues/",
        json={
            "project_id": proj_id,
            "title": title,
            "status": status,
            "story_points": story_points,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


def _create_report(client, auth_headers, proj_id, hours=8.0, days_ago=0):
    report_date = (date.today() - timedelta(days=days_ago)).isoformat()
    resp = client.post(
        "/reports/",
        json={
            "project_id": proj_id,
            "report_date": report_date,
            "hours_spent": hours,
            "category": "dev",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


# ─── Progress ────────────────────────────────────────────────────────────────


def test_progress_empty_project(client, test_project):
    resp = client.get(f"/projects/{test_project['id']}/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_issues"] == 0
    assert data["progress_pct"] == 0.0


def test_progress_with_issues(client, test_project, auth_headers):
    _create_issue(client, auth_headers, test_project["id"], "Open1", status="open")
    _create_issue(client, auth_headers, test_project["id"], "Open2", status="open")
    _create_issue(client, auth_headers, test_project["id"], "Done", status="closed")

    resp = client.get(f"/projects/{test_project['id']}/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_issues"] == 3
    assert data["closed_issues"] == 1
    assert data["open_issues"] == 2
    assert abs(data["progress_pct"] - 33.3) < 0.5


def test_progress_project_not_found(client):
    assert client.get("/projects/9999/progress").status_code == 404


# ─── Velocity ────────────────────────────────────────────────────────────────


def test_velocity_returns_n_weeks(client, test_project):
    resp = client.get(f"/projects/{test_project['id']}/velocity?weeks=4")
    assert resp.status_code == 200
    assert len(resp.json()) == 4


def test_velocity_counts_closed_issues(client, test_project, auth_headers, db_session):
    issue = _create_issue(
        client, auth_headers, test_project["id"], "Closed this week", status="closed"
    )

    # Ensure closed_at falls within the current week
    row = db_session.query(Issue).filter(Issue.id == issue["id"]).first()
    row.closed_at = datetime.now(timezone.utc)
    db_session.commit()

    resp = client.get(f"/projects/{test_project['id']}/velocity?weeks=1")
    assert resp.status_code == 200
    assert resp.json()[0]["closed_issues"] >= 1


# ─── Stale Issues ────────────────────────────────────────────────────────────


def test_stale_issues_empty(client, test_project):
    resp = client.get(f"/projects/{test_project['id']}/stale-issues")
    assert resp.status_code == 200
    assert resp.json() == []


def test_stale_issues_detected(client, test_project, auth_headers, db_session):
    issue = _create_issue(
        client, auth_headers, test_project["id"], "Stuck task", status="in_progress"
    )

    row = db_session.query(Issue).filter(Issue.id == issue["id"]).first()
    row.updated_at = datetime.now(timezone.utc) - timedelta(days=10)
    db_session.commit()

    resp = client.get(f"/projects/{test_project['id']}/stale-issues?stale_days=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == issue["id"]
    assert data[0]["days_stale"] >= 10


# ─── User Workload ───────────────────────────────────────────────────────────


def test_workload_no_reports(client, registered_user):
    resp = client.get(f"/users/{registered_user['id']}/workload")
    assert resp.status_code == 200
    data = resp.json()
    assert data["weekly_hours"] == 0.0
    assert data["at_risk"] is False


def test_workload_at_risk(client, test_project, registered_user, auth_headers):
    for i in range(6):
        _create_report(
            client,
            auth_headers,
            test_project["id"],
            hours=8.0,
            days_ago=i,
        )

    resp = client.get(f"/users/{registered_user['id']}/workload")
    assert resp.status_code == 200
    data = resp.json()
    assert data["weekly_hours"] == 48.0
    assert data["at_risk"] is True
    assert data["risk_reason"] is not None


def test_workload_user_not_found(client):
    assert client.get("/users/9999/workload").status_code == 404


# ─── Dashboard ───────────────────────────────────────────────────────────────


def test_dashboard(client, test_project, registered_user, auth_headers):
    _create_issue(client, auth_headers, test_project["id"], "Issue A", status="open")
    _create_issue(client, auth_headers, test_project["id"], "Issue B", status="closed")
    _create_report(client, auth_headers, test_project["id"], hours=5.0)

    resp = client.get(f"/projects/{test_project['id']}/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == test_project["id"]
    assert data["spent_hours"] == 5.0
    assert data["progress"]["total_issues"] == 2
    assert len(data["velocity"]) == 6
    assert "hours_by_category" in data
    assert "issues_by_type" in data


def test_dashboard_project_not_found(client):
    assert client.get("/projects/9999/dashboard").status_code == 404


# ─── GitLab Sync ─────────────────────────────────────────────────────────────


def test_sync_gitlab(client, test_project, auth_headers):
    payload = {
        "project_id": test_project["id"],
        "issues": [
            {"id": 100, "title": "Fix crash", "state": "opened", "labels": []},
            {"id": 101, "title": "Add feature", "state": "closed", "labels": []},
        ],
    }
    resp = client.post(
        f"/projects/{test_project['id']}/sync/gitlab",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 2
    assert data["updated"] == 0

    # Re-sync same issues → should update
    resp2 = client.post(
        f"/projects/{test_project['id']}/sync/gitlab",
        json=payload,
        headers=auth_headers,
    )
    assert resp2.json()["updated"] == 2


# ─── Jira Sync ───────────────────────────────────────────────────────────────


def test_sync_jira(client, test_project, auth_headers):
    payload = {
        "project_id": test_project["id"],
        "issues": [
            {
                "key": "PROJ-1",
                "summary": "Login bug",
                "status": "In Progress",
                "issuetype": "Bug",
            },
            {
                "key": "PROJ-2",
                "summary": "Dashboard feature",
                "status": "Done",
                "issuetype": "Story",
            },
        ],
    }
    resp = client.post(
        f"/projects/{test_project['id']}/sync/jira", json=payload, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 2
    assert data["total"] == 2
