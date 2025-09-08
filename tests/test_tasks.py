from datetime import date, timedelta

def test_create_task(client, user_token_headers):
    resp = client.post("/tasks/", json={"title": "Task 1", "description": "Desc"}, headers=user_token_headers)
    assert resp.status_code == 201
    assert resp.json()["title"] == "Task 1"


def test_list_tasks_pagination(client, user_token_headers):
    for i in range(5):
        client.post("/tasks/", json={"title": f"T{i}"}, headers=user_token_headers)
    resp = client.get("/tasks?limit=2&offset=0", headers=user_token_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 5
    assert len(data["items"]) == 2


def test_search_tasks_q(client, user_token_headers):
    client.post("/tasks/", json={"title": "UniqueAlpha"}, headers=user_token_headers)
    resp = client.get("/tasks?q=UniqueAlpha", headers=user_token_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(task["title"] == "UniqueAlpha" for task in items)


def test_ownership_protection(client, user_token_headers):
    # create second user
    resp2 = client.post("/auth/register", json={"email": "other@example.com", "password": "password123"})
    assert resp2.status_code == 201
    # login second user
    login2 = client.post("/auth/login", data={"username": "other@example.com", "password": "password123"}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    token2 = login2.json()["access_token"]
    hdr2 = {"Authorization": f"Bearer {token2}"}

    # first user creates task
    t = client.post("/tasks/", json={"title": "Private Task"}, headers=user_token_headers).json()
    # second tries to fetch
    resp_forbidden = client.get(f"/tasks/{t['id']}", headers=hdr2)
    assert resp_forbidden.status_code == 403


def test_admin_list_all(client, admin_token_headers, user_token_headers):
    # create tasks under normal user
    client.post("/tasks/", json={"title": "A1"}, headers=user_token_headers)
    client.post("/tasks/", json={"title": "A2"}, headers=user_token_headers)
    # admin creates its own
    client.post("/tasks/", json={"title": "AdminT"}, headers=admin_token_headers)

    resp_admin = client.get("/tasks?all=true", headers=admin_token_headers)
    assert resp_admin.status_code == 200
    data = resp_admin.json()
    titles = [t["title"] for t in data["items"]]
    assert any(x in titles for x in ["A1", "A2"]) and "AdminT" in titles
