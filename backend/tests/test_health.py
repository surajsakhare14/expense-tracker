def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["content-type"].startswith("application/json")


def test_health_returns_request_id(client):
    response = client.get("/health", headers={"X-Request-ID": "test-request"})

    assert response.headers["X-Request-ID"] == "test-request"