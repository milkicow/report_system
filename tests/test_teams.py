def test_list_teams_empty(client):
    resp = client.get("/teams/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_team(client, auth_headers):
    resp = client.post("/teams/", json={"name": "Alpha"}, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alpha"
    assert data["members"] == []


def test_create_team_requires_auth(client):
    resp = client.post("/teams/", json={"name": "Alpha"})
    assert resp.status_code == 401


def test_get_team(client, auth_headers):
    team = client.post("/teams/", json={"name": "Beta"}, headers=auth_headers).json()
    resp = client.get(f"/teams/{team['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Beta"


def test_get_team_not_found(client):
    assert client.get("/teams/9999").status_code == 404


def test_update_team(client, auth_headers):
    team = client.post("/teams/", json={"name": "Gamma"}, headers=auth_headers).json()
    resp = client.patch(
        f"/teams/{team['id']}", json={"name": "Gamma v2"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Gamma v2"


def test_duplicate_team_name(client, auth_headers):
    client.post("/teams/", json={"name": "Unique"}, headers=auth_headers)
    resp = client.post("/teams/", json={"name": "Unique"}, headers=auth_headers)
    assert resp.status_code == 409


def test_add_team_member(client, auth_headers, registered_user):
    team = client.post("/teams/", json={"name": "Delta"}, headers=auth_headers).json()
    resp = client.post(
        f"/teams/{team['id']}/members",
        json={"user_id": registered_user["id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["user_id"] == registered_user["id"]


def test_add_duplicate_team_member(client, auth_headers, registered_user):
    team = client.post("/teams/", json={"name": "Epsilon"}, headers=auth_headers).json()
    payload = {"user_id": registered_user["id"]}
    client.post(f"/teams/{team['id']}/members", json=payload, headers=auth_headers)
    resp = client.post(
        f"/teams/{team['id']}/members", json=payload, headers=auth_headers
    )
    assert resp.status_code == 409


def test_remove_team_member(client, auth_headers, registered_user):
    team = client.post("/teams/", json={"name": "Zeta"}, headers=auth_headers).json()
    client.post(
        f"/teams/{team['id']}/members",
        json={"user_id": registered_user["id"]},
        headers=auth_headers,
    )
    resp = client.delete(
        f"/teams/{team['id']}/members/{registered_user['id']}", headers=auth_headers
    )
    assert resp.status_code == 204


def test_delete_team(client, auth_headers):
    team = client.post(
        "/teams/", json={"name": "ToDelete"}, headers=auth_headers
    ).json()
    resp = client.delete(f"/teams/{team['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get(f"/teams/{team['id']}").status_code == 404
