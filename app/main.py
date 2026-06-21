"""카카오톡 × Claude 챗봇 스킬 서버 (FastAPI).

동작 흐름
---------
1. 카카오 i 오픈빌더가 사용자 발화를 이 서버의 POST /skill 로 전달한다.
2. 콜백(callbackUrl)이 있으면: 즉시 "대기" 응답을 돌려주고(5초 제한 회피),
   백그라운드에서 Claude 답변을 만들어 callbackUrl 로 전송한다(1분 이내).
3. 콜백이 없으면: 동기적으로 Claude를 호출해 5초 이내에 답변한다.
"""

import asyncio
import logging

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import claude_client, conversation, kakao
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kakao-claude")

app = FastAPI(title="KakaoTalk × Claude Skill Server")

RESET_COMMANDS = {"초기화", "리셋", "/reset", "처음으로"}


@app.get("/")
async def root():
    return {"service": "kakao-claude-skill", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.claude_model}


@app.post("/skill")
async def skill(request: Request):
    """카카오 오픈빌더 스킬 웹훅 엔드포인트."""
    body = await request.json()
    user_request = body.get("userRequest", {})
    utterance = (user_request.get("utterance") or "").strip()
    user_id = (user_request.get("user") or {}).get("id", "anonymous")
    callback_url = user_request.get("callbackUrl")

    if not utterance:
        return JSONResponse(kakao.simple_text("무엇을 도와드릴까요?"))

    if utterance in RESET_COMMANDS:
        conversation.reset(user_id)
        return JSONResponse(
            kakao.simple_text("대화 내용을 초기화했어요. 새로 시작해볼까요? 😊")
        )

    # 콜백을 쓸 수 있으면 비동기 처리 (LLM 응답이 5초를 넘겨도 안전)
    if callback_url:
        asyncio.create_task(_handle_callback(user_id, utterance, callback_url))
        return JSONResponse(
            kakao.callback_wait("답변을 준비하고 있어요 🤔 잠시만 기다려 주세요!")
        )

    # 콜백이 비활성화된 경우: 5초 이내 동기 응답
    answer = await _safe_generate(user_id, utterance)
    return JSONResponse(kakao.simple_text(answer))


async def _handle_callback(user_id: str, utterance: str, callback_url: str) -> None:
    """백그라운드에서 답변을 만들어 카카오 callbackUrl 로 전송."""
    answer = await _safe_generate(user_id, utterance)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(callback_url, json=kakao.simple_text(answer))
            resp.raise_for_status()
    except Exception:
        logger.exception("카카오 콜백 전송 실패")


async def _safe_generate(user_id: str, utterance: str) -> str:
    """Claude 호출을 타임아웃/예외로부터 보호하여 항상 문자열을 반환."""
    try:
        messages = conversation.get_messages(user_id, utterance)
        answer = await asyncio.wait_for(
            claude_client.generate(messages), timeout=settings.request_timeout
        )
        conversation.record(user_id, utterance, answer)
        return answer
    except asyncio.TimeoutError:
        logger.warning("Claude 응답 타임아웃 (user=%s)", user_id)
        return "답변 생성이 조금 오래 걸리고 있어요. 잠시 후 다시 시도해 주세요 🙏"
    except Exception:
        logger.exception("Claude 응답 생성 실패")
        return "일시적인 오류가 발생했어요. 잠시 후 다시 시도해 주세요 🙏"
