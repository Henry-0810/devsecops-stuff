import pytest


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/", "/ideas"])
def test_html_pages(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<html" in response.text.lower()


def test_idea_lifecycle(client):
    assert client.get("/api/ideas").json() == []
    response = client.post(
        "/api/ideas", json={"title": "  Delivery  ", "description": "First version"}
    )
    assert response.status_code == 201
    idea = response.json()
    assert idea == {
        "id": idea["id"],
        "title": "Delivery",
        "description": "First version",
    }
    path = f"/api/ideas/{idea['id']}"
    assert client.get(path).json() == idea
    assert client.get("/api/ideas").json() == [idea]

    response = client.put(path, json={"title": "Updated"})
    assert response.status_code == 200
    updated = {**idea, "title": "Updated"}
    assert response.json() == updated
    assert client.get(path).json() == updated
    assert client.put(path, json={}).json() == updated
    assert client.put(path, json={"description": None}).json()["description"] is None

    response = client.delete(path)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(path).status_code == 404
    assert client.get("/api/ideas").json() == []


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_idea(client, method):
    kwargs = {"json": {"title": "Missing"}} if method == "put" else {}
    response = getattr(client, method)("/api/ideas/999", **kwargs)
    assert response.status_code == 404
    assert response.json() == {"detail": "Idea not found"}


@pytest.mark.parametrize("title", [None, "", "  ", "x" * 121])
def test_invalid_create_does_not_write(client, title):
    assert client.post("/api/ideas", json={"title": title}).status_code == 422
    assert client.get("/api/ideas").json() == []


@pytest.mark.parametrize("title", [None, "", "  ", "x" * 121])
def test_invalid_update_keeps_existing_idea(client, title):
    idea = client.post("/api/ideas", json={"title": "Original"}).json()
    path = f"/api/ideas/{idea['id']}"
    assert client.put(path, json={"title": title}).status_code == 422
    assert client.get(path).json() == idea


def test_database_survives_reinitialization(client, app_module):
    idea = client.post("/api/ideas", json={"title": "Persistent"}).json()
    app_module.initialize_database()
    assert client.get(f"/api/ideas/{idea['id']}").json() == idea
