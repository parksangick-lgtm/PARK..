"""스킬 서버 동작 테스트 (Claude 호출은 목 처리)."""

import asyncio

from fastapi.testclient import TestClient

from app import claude_client, conversation, kakao, main


def _patch_generate(monkeypatch, reply="안녕하세요! 무엇을 도와드릴까요?"):
    async def fake_generate(messages):
        return reply

    monkeypatch.setattr(claude_client, "generate", fake_generate)


def test_health():
    client = TestClient(main.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_skill_sync_without_callback(monkeypatch):
    _patch_generate(monkeypatch, "테스트 답변")
    client = TestClient(main.app)

    resp = client.post(
        "/skill",
        json={"userRequest": {"utterance": "안녕", "user": {"id": "u1"}}},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["template"]["outputs"][0]["simpleText"]["text"] == "테스트 답변"


def test_skill_with_callback_returns_wait(monkeypatch):
    _patch_generate(monkeypatch)
    client = TestClient(main.app)

    resp = client.post(
        "/skill",
        json={
            "userRequest": {
                "utterance": "안녕",
                "user": {"id": "u2"},
                "callbackUrl": "https://example.com/callback",
            }
        },
    )

    assert resp.status_code == 200
    assert resp.json()["useCallback"] is True


def test_reset_command(monkeypatch):
    _patch_generate(monkeypatch)
    client = TestClient(main.app)
    conversation.record("u3", "이전", "기록")

    resp = client.post(
        "/skill",
        json={"userRequest": {"utterance": "초기화", "user": {"id": "u3"}}},
    )

    assert resp.status_code == 200
    assert "초기화" in resp.json()["template"]["outputs"][0]["simpleText"]["text"]
    assert conversation.get_messages("u3", "다음") == [
        {"role": "user", "content": "다음"}
    ]


def test_empty_utterance(monkeypatch):
    _patch_generate(monkeypatch)
    client = TestClient(main.app)
    resp = client.post("/skill", json={"userRequest": {"utterance": "", "user": {"id": "u4"}}})
    assert resp.status_code == 200


def test_long_answer_is_split_into_bubbles():
    long_text = "가" * 2500
    payload = kakao.simple_text(long_text)
    outputs = payload["template"]["outputs"]
    assert 1 < len(outputs) <= kakao.KAKAO_MAX_OUTPUTS
    for out in outputs:
        assert len(out["simpleText"]["text"]) <= kakao.KAKAO_TEXT_LIMIT


def test_conversation_history_roundtrip():
    conversation.reset("u5")
    conversation.record("u5", "내 이름은 박상익", "반갑습니다")
    messages = conversation.get_messages("u5", "내 이름이 뭐야?")
    assert messages[0] == {"role": "user", "content": "내 이름은 박상익"}
    assert messages[-1] == {"role": "user", "content": "내 이름이 뭐야?"}
