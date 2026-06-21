"""환경변수 기반 설정."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Anthropic / Claude
    anthropic_api_key: str = ""
    claude_model: str = "claude-opus-4-8"
    max_tokens: int = 2048
    enable_thinking: bool = True
    system_prompt: str = (
        "당신은 카카오톡 채널에서 사용자를 돕는 친절한 AI 어시스턴트입니다. "
        "한국어로 자연스럽고 간결하게 답변하세요. "
        "카카오톡 메시지는 길면 잘릴 수 있으니 답변은 가능한 한 1000자 이내로 작성하세요."
    )

    # 대화 / 동작
    history_max_turns: int = 6
    request_timeout: float = 50.0


settings = Settings()
