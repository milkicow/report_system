USER = {
    "name": "Alice",
    "email": "alice@test.com",
    "password": "secret123",
    "role": "developer",
}


def test_register_success(client):
    resp = client.post("/auth/register", json=USER)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == USER["email"]
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client):
    client.post("/auth/register", json=USER)
    resp = client.post("/auth/register", json=USER)
    assert resp.status_code == 409


def test_login_success(client):
    client.post("/auth/register", json=USER)
    resp = client.post(
        "/auth/token", data={"username": USER["email"], "password": USER["password"]}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post("/auth/register", json=USER)
    resp = client.post(
        "/auth/token", data={"username": USER["email"], "password": "wrong"}
    )
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post(
        "/auth/token", data={"username": "nobody@test.com", "password": "x"}
    )
    assert resp.status_code == 401


def test_protected_endpoint_without_token(client):
    resp = client.post("/projects/", json={"name": "P"})
    assert resp.status_code == 401


def test_protected_endpoint_with_invalid_token(client):
    resp = client.post(
        "/projects/",
        json={"name": "P"},
        headers={"Authorization": "Bearer not.a.real.token"},
    )
    assert resp.status_code == 401


def test_protected_endpoint_with_valid_token(client):
    client.post("/auth/register", json=USER)
    token_resp = client.post(
        "/auth/token", data={"username": USER["email"], "password": USER["password"]}
    )
    token = token_resp.json()["access_token"]

    resp = client.post(
        "/projects/",
        json={"name": "My Project", "budget_hours": 50.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "My Project"
