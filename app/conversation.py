"""사용자별 대화 기록 관리(인메모리).

주의: 프로세스 메모리에만 저장되므로 서버 재시작 시 사라지고,
여러 인스턴스로 확장하려면 Redis 등 외부 저장소로 교체해야 한다.
"""

from collections import defaultdict, deque

from .config import settings


def _new_deque() -> deque:
    # user/assistant 한 쌍이 한 턴이므로 maxlen 은 턴 수 * 2
    return deque(maxlen=settings.history_max_turns * 2)


_history: dict[str, deque] = defaultdict(_new_deque)


def get_messages(user_id: str, utterance: str) -> list[dict]:
    """저장된 히스토리 + 이번 사용자 발화로 messages 배열을 구성."""
    return list(_history[user_id]) + [{"role": "user", "content": utterance}]


def record(user_id: str, utterance: str, answer: str) -> None:
    """이번 턴(사용자 발화 + 봇 답변)을 히스토리에 추가."""
    history = _history[user_id]
    history.append({"role": "user", "content": utterance})
    history.append({"role": "assistant", "content": answer})


def reset(user_id: str) -> None:
    """해당 사용자의 대화 기록을 삭제."""
    _history.pop(user_id, None)
