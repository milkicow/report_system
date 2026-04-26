def test_create_project(client, auth_headers):
    resp = client.post(
        "/projects/",
        json={"name": "Proj A", "budget_hours": 200.0},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Proj A"
    assert data["budget_hours"] == 200.0
    assert data["status"] == "active"


def test_create_project_requires_auth(client):
    resp = client.post("/projects/", json={"name": "Proj"})
    assert resp.status_code == 401


def test_list_projects(client, auth_headers):
    client.post("/projects/", json={"name": "P1"}, headers=auth_headers)
    client.post("/projects/", json={"name": "P2"}, headers=auth_headers)
    resp = client.get("/projects/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_projects_filter_by_status(client, auth_headers):
    client.post(
        "/projects/", json={"name": "Active", "status": "active"}, headers=auth_headers
    )
    client.post(
        "/projects/", json={"name": "Done", "status": "completed"}, headers=auth_headers
    )
    resp = client.get("/projects/?status=completed")
    assert resp.status_code == 200
    assert all(p["status"] == "completed" for p in resp.json())


def test_get_project(client, test_project):
    resp = client.get(f"/projects/{test_project['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == test_project["id"]


def test_get_project_not_found(client):
    assert client.get("/projects/9999").status_code == 404


def test_update_project(client, test_project, auth_headers):
    resp = client.patch(
        f"/projects/{test_project['id']}",
        json={"status": "completed", "budget_hours": 150.0},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["budget_hours"] == 150.0


def test_delete_project(client, auth_headers):
    proj = client.post(
        "/projects/", json={"name": "ToDelete"}, headers=auth_headers
    ).json()
    resp = client.delete(f"/projects/{proj['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get(f"/projects/{proj['id']}").status_code == 404


def test_add_project_member(client, test_project, registered_user, auth_headers):
    resp = client.post(
        f"/projects/{test_project['id']}/members",
        json={"user_id": registered_user["id"], "member_role": "developer"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["user_id"] == registered_user["id"]


def test_add_duplicate_project_member(
    client, test_project, registered_user, auth_headers
):
    payload = {"user_id": registered_user["id"]}
    client.post(
        f"/projects/{test_project['id']}/members", json=payload, headers=auth_headers
    )
    resp = client.post(
        f"/projects/{test_project['id']}/members", json=payload, headers=auth_headers
    )
    assert resp.status_code == 409


def test_remove_project_member(client, test_project, registered_user, auth_headers):
    client.post(
        f"/projects/{test_project['id']}/members",
        json={"user_id": registered_user["id"]},
        headers=auth_headers,
    )
    resp = client.delete(
        f"/projects/{test_project['id']}/members/{registered_user['id']}",
        headers=auth_headers,
    )
    assert resp.status_code == 204
