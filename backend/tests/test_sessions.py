VALID_BODY = {"age_group": "7-9", "topic": "animals"}


def _create(client, body=VALID_BODY):
    return client.post("/api/sessions", json=body)


def test_create_session_returns_greeting(client):
    res = _create(client)

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["session_id"]
    assert data["assistant_text"]
    assert data["state"] == "greeting"
    assert data["turn"] == 0
    assert data["finished"] is False
    assert data["max_turns"] == 4


def test_create_session_rejects_invalid_topic(client):
    res = _create(client, {"age_group": "7-9", "topic": "cars"})

    assert res.status_code == 422
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"


def test_create_session_rejects_invalid_age_group(client):
    res = _create(client, {"age_group": "3-4", "topic": "animals"})

    assert res.status_code == 422
    assert res.json()["success"] is False


def test_reply_advances_turn(client):
    sid = _create(client).json()["data"]["session_id"]

    res = client.post(f"/api/sessions/{sid}/replies", json={"text": "I like dogs"})

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["turn"] == 1
    assert data["finished"] is False
    assert data["assistant_text"]


def test_reply_finishes_after_max_turns(client):
    sid = _create(client).json()["data"]["session_id"]

    last = None
    for _ in range(4):
        last = client.post(
            f"/api/sessions/{sid}/replies", json={"text": "hello"}
        ).json()["data"]

    assert last["turn"] == 4
    assert last["finished"] is True
    assert last["state"] == "praise"

    after = client.post(
        f"/api/sessions/{sid}/replies", json={"text": "hello"}
    ).json()["data"]
    assert after["finished"] is True


def test_reply_unknown_session_404(client):
    res = client.post("/api/sessions/does-not-exist/replies", json={"text": "hi"})

    assert res.status_code == 404
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "session_not_found"


def test_end_session_deletes_context(client):
    sid = _create(client).json()["data"]["session_id"]

    end = client.post(f"/api/sessions/{sid}/end")

    assert end.status_code == 200
    assert end.json()["data"]["ended"] is True

    res = client.post(f"/api/sessions/{sid}/replies", json={"text": "hi"})
    assert res.status_code == 404


def test_reply_rejects_empty_text(client):
    sid = _create(client).json()["data"]["session_id"]

    empty = client.post(f"/api/sessions/{sid}/replies", json={"text": ""})
    blank = client.post(f"/api/sessions/{sid}/replies", json={"text": "   "})

    assert empty.status_code == 422
    assert empty.json()["success"] is False
    assert blank.status_code == 422
    assert blank.json()["success"] is False
