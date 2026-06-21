"""Claude(Anthropic) API 호출 래퍼."""

import anthropic

from .config import settings

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    """AsyncAnthropic 클라이언트를 지연 생성한다.

    import 시점에 API 키가 없어도 테스트가 가능하도록 lazy 초기화한다.
    """
    global _client
    if _client is None:
        if settings.anthropic_api_key:
            _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        else:
            # ANTHROPIC_API_KEY 환경변수에서 자동으로 읽음
            _client = anthropic.AsyncAnthropic()
    return _client


async def generate(messages: list[dict]) -> str:
    """대화 메시지 목록을 받아 Claude 답변 텍스트를 돌려준다."""
    kwargs: dict = {
        "model": settings.claude_model,
        "max_tokens": settings.max_tokens,
        "system": settings.system_prompt,
        "messages": messages,
    }
    if settings.enable_thinking:
        # Opus 4.8 / 4.7 / 4.6, Sonnet 4.6 등 최신 모델은 adaptive thinking 사용
        kwargs["thinking"] = {"type": "adaptive"}

    response = await _get_client().messages.create(**kwargs)
    return _extract_text(response)


def _extract_text(response) -> str:
    """응답 content 블록에서 text 블록만 추려 합친다(thinking 블록은 제외)."""
    parts = [block.text for block in response.content if block.type == "text"]
    text = "\n".join(parts).strip()
    return text or "죄송해요, 답변을 생성하지 못했어요. 다시 한 번 말씀해 주시겠어요?"
