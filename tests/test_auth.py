def test_register_success(client):
    resp = client.post("/auth/register", json={"email": "newuser@example.com", "password": "password123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data


def test_register_duplicate(client):
    client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})
    resp = client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})
    assert resp.status_code == 400


def test_login_success(client):
    client.post("/auth/register", json={"email": "login@example.com", "password": "password123"})
    resp = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "wrongpw@example.com", "password": "password123"})
    resp = client.post(
        "/auth/login",
        data={"username": "wrongpw@example.com", "password": "badpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401
