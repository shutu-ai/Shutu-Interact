def test_health_returns_ok(client):
    res = client.get("/api/health")

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["app"] == "coco-english"
