def _make_issue(
    client, auth_headers, project_id, title="Fix bug", status="open", priority="medium"
):
    return client.post(
        "/issues/",
        json={
            "project_id": project_id,
            "title": title,
            "status": status,
            "priority": priority,
            "story_points": 3,
        },
        headers=auth_headers,
    )


def test_create_issue(client, test_project, auth_headers):
    resp = _make_issue(client, auth_headers, test_project["id"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Fix bug"
    assert data["status"] == "open"
    assert data["closed_at"] is None


def test_create_issue_requires_auth(client, test_project):
    resp = client.post(
        "/issues/", json={"project_id": test_project["id"], "title": "X"}
    )
    assert resp.status_code == 401


def test_get_issue(client, test_project, auth_headers):
    issue = _make_issue(client, auth_headers, test_project["id"]).json()
    resp = client.get(f"/issues/{issue['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == issue["id"]


def test_get_issue_not_found(client):
    assert client.get("/issues/9999").status_code == 404


def test_create_closed_issue_sets_closed_at(client, test_project, auth_headers):
    resp = _make_issue(client, auth_headers, test_project["id"], status="closed")
    assert resp.status_code == 201
    assert resp.json()["closed_at"] is not None


def test_update_issue_to_closed_sets_closed_at(client, test_project, auth_headers):
    issue = _make_issue(client, auth_headers, test_project["id"]).json()
    assert issue["closed_at"] is None

    resp = client.patch(
        f"/issues/{issue['id']}", json={"status": "closed"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["closed_at"] is not None


def test_reopen_issue_clears_closed_at(client, test_project, auth_headers):
    issue = _make_issue(
        client, auth_headers, test_project["id"], status="closed"
    ).json()
    assert issue["closed_at"] is not None

    resp = client.patch(
        f"/issues/{issue['id']}", json={"status": "in_progress"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["closed_at"] is None


def test_list_issues_filter_status(client, test_project, auth_headers):
    _make_issue(client, auth_headers, test_project["id"], title="Open", status="open")
    _make_issue(
        client, auth_headers, test_project["id"], title="Closed", status="closed"
    )

    resp = client.get(f"/issues/?status=open&project_id={test_project['id']}")
    assert resp.status_code == 200
    assert all(i["status"] == "open" for i in resp.json())


def test_list_issues_filter_priority(client, test_project, auth_headers):
    _make_issue(
        client, auth_headers, test_project["id"], title="Critical", priority="critical"
    )
    _make_issue(client, auth_headers, test_project["id"], title="Low", priority="low")

    resp = client.get(f"/issues/?priority=critical&project_id={test_project['id']}")
    assert resp.status_code == 200
    assert all(i["priority"] == "critical" for i in resp.json())


def test_delete_issue(client, test_project, auth_headers):
    issue = _make_issue(client, auth_headers, test_project["id"]).json()
    resp = client.delete(f"/issues/{issue['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get(f"/issues/{issue['id']}").status_code == 404


def test_create_issue_with_assignee(
    client, test_project, registered_user, auth_headers
):
    resp = client.post(
        "/issues/",
        json={
            "project_id": test_project["id"],
            "title": "Assigned task",
            "assignee_id": registered_user["id"],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["assignee_id"] == registered_user["id"]
    assert resp.json()["assignee"]["email"] == registered_user["email"]
