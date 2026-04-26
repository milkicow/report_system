def test_list_users_returns_registered(client, registered_user):
    resp = client.get("/users/")
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert registered_user["email"] in emails


def test_create_user_requires_auth(client):
    resp = client.post(
        "/users/", json={"name": "X", "email": "x@x.com", "password": "password1"}
    )
    assert resp.status_code == 401


def test_create_user_success(client, auth_headers):
    resp = client.post(
        "/users/",
        json={
            "name": "Bob",
            "email": "bob@test.com",
            "password": "pass1234",
            "role": "developer",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Bob"
    assert data["role"] == "developer"
    assert "password_hash" not in data


def test_get_user(client, registered_user):
    resp = client.get(f"/users/{registered_user['id']}")
    assert resp.status_code == 200
    assert resp.json()["email"] == registered_user["email"]


def test_get_user_not_found(client):
    resp = client.get("/users/9999")
    assert resp.status_code == 404


def test_update_user_requires_auth(client, registered_user):
    resp = client.patch(f"/users/{registered_user['id']}", json={"name": "New Name"})
    assert resp.status_code == 401


def test_update_user(client, registered_user, auth_headers):
    resp = client.patch(
        f"/users/{registered_user['id']}",
        json={"name": "Updated Name"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


def test_delete_user_requires_auth(client, dev_user):
    resp = client.delete(f"/users/{dev_user['id']}")
    assert resp.status_code == 401


def test_delete_user(client, dev_user, auth_headers):
    resp = client.delete(f"/users/{dev_user['id']}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get(f"/users/{dev_user['id']}")
    assert resp.status_code == 404
