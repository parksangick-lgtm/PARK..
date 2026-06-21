"""카카오 i 오픈빌더 스킬 요청/응답 포맷 헬퍼.

카카오 스킬 응답 규격:
https://kakaobusiness.gitbook.io/main/tool/chatbot/skill_guide/answer_json_format
"""

# simpleText 한 말풍선의 최대 길이, 그리고 template.outputs 최대 개수
KAKAO_TEXT_LIMIT = 1000
KAKAO_MAX_OUTPUTS = 3


def simple_text(text: str) -> dict:
    """일반 스킬 응답(SkillResponse)을 만든다.

    1000자가 넘는 답변은 여러 개의 말풍선으로 자동 분할한다(최대 3개).
    """
    chunks = _split(text, KAKAO_TEXT_LIMIT, KAKAO_MAX_OUTPUTS)
    return {
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": c}} for c in chunks]},
    }


def callback_wait(text: str) -> dict:
    """콜백 사용 시 즉시 돌려주는 '대기' 응답.

    이 응답을 5초 이내에 돌려준 뒤, 실제 답변은 1분 이내에
    userRequest.callbackUrl 로 simple_text() 형태로 POST 한다.
    """
    return {"version": "2.0", "useCallback": True, "data": {"text": text}}


def _split(text: str, size: int, max_chunks: int) -> list[str]:
    """긴 텍스트를 size 길이 단위로, 가능하면 줄바꿈/공백 경계에서 분할."""
    text = (text or "").strip()
    if not text:
        return [""]

    chunks: list[str] = []
    while text and len(chunks) < max_chunks:
        if len(text) <= size:
            chunks.append(text)
            text = ""
            break

        cut = text.rfind("\n", 0, size)
        if cut < size // 2:
            cut = text.rfind(" ", 0, size)
        if cut < size // 2:
            cut = size

        chunks.append(text[:cut].strip())
        text = text[cut:].strip()

    if text:  # max_chunks 를 넘긴 잔여 텍스트는 말줄임 처리
        last = chunks[-1]
        chunks[-1] = last[: size - 1].rstrip() + "…"

    return chunks
