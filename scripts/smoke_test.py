"""Run inside a fresh container; uses only Python's standard library."""

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request(path, method="GET", payload=None, expected_status=200):
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(
        "http://127.0.0.1:8080" + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        response = urlopen(req, timeout=5)
    except HTTPError as error:
        response = error
    with response:
        body = response.read().decode()
        assert response.status == expected_status, (method, path, response.status, body)
        if body and "application/json" in response.headers.get("Content-Type", ""):
            return json.loads(body)
        return body


def main():
    assert request("/health") == {"status": "ok"}
    for path in ("/", "/ideas"):
        assert "<html" in request(path).lower()
    assert request("/api/ideas") == []
    idea = request(
        "/api/ideas",
        "POST",
        {"title": "CI smoke test", "description": "Check SQLite writes"},
        expected_status=201,
    )
    assert idea["title"] == "CI smoke test"
    path = f"/api/ideas/{idea['id']}"
    assert request(path) == idea
    assert request("/api/ideas") == [idea]
    updated = request(path, "PUT", {"title": "Updated idea"})
    assert updated == {**idea, "title": "Updated idea"}
    assert request(path) == updated
    request("/api/ideas", "POST", {"title": "   "}, expected_status=422)
    request(path, "DELETE", expected_status=204)
    request(path, expected_status=404)
    assert request("/api/ideas") == []
    print("All container smoke checks passed.")


if __name__ == "__main__":
    main()
