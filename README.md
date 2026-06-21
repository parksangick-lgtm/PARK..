# 카카오톡 × Claude 챗봇 (스킬 서버)

카카오톡 채널 챗봇에 **Claude(Anthropic)** 를 두뇌로 연결하는 FastAPI 스킬 서버입니다.
사용자가 카카오톡 채널 챗봇에게 메시지를 보내면 → 이 서버가 Claude API를 호출하고 →
답변을 카카오톡으로 돌려줍니다.

```
사용자 ─(메시지)→ 카카오톡 채널 ─(웹훅)→ 카카오 i 오픈빌더 ─(스킬 요청)→ [이 서버] ─→ Claude API
                                                              ↑                          │
                                                              └────────(답변)────────────┘
```

## ✨ 특징

- **카카오 i 오픈빌더 스킬 서버** 규격(`version 2.0`) 준수
- **콜백(Callback) 지원** — Claude 응답이 카카오 5초 제한을 넘겨도 안전 (최대 1분)
- **사용자별 대화 맥락 기억** (인메모리, 최근 N턴)
- 긴 답변은 카카오 말풍선(최대 3개, 각 1000자)으로 **자동 분할**
- `초기화` / `리셋` 명령으로 대화 리셋
- 모델·페르소나·thinking 여부를 **환경변수로 설정**

---

## 1. 사전 준비물

| 항목 | 설명 |
|------|------|
| Anthropic API 키 | <https://console.anthropic.com> 에서 발급 |
| 카카오 비즈니스 채널 | <https://center-pf.kakao.com> 에서 채널 생성 |
| 카카오 i 오픈빌더 | <https://i.kakao.com> 에서 봇 생성 (채널 연결) |
| 공개 가능한 서버 URL | 오픈빌더가 호출할 수 있는 HTTPS 주소 (배포 또는 ngrok) |
| Python 3.10+ | |

---

## 2. 설치 및 실행

```bash
# 1) 의존성 설치
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) 환경변수 설정
cp .env.example .env
#   .env 파일을 열어 ANTHROPIC_API_KEY 등을 채워 넣으세요.

# 3) 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

동작 확인:

```bash
curl http://localhost:8000/health
# {"status":"ok","model":"claude-opus-4-8"}
```

스킬 요청 형식으로 직접 테스트:

```bash
curl -X POST http://localhost:8000/skill \
  -H "Content-Type: application/json" \
  -d '{"userRequest": {"utterance": "안녕! 너는 누구야?", "user": {"id": "tester"}}}'
```

---

## 3. 외부에 공개하기

오픈빌더는 **공개된 HTTPS URL** 로만 스킬 서버를 호출할 수 있습니다.

- **로컬 테스트**: [ngrok](https://ngrok.com) 등으로 터널링
  ```bash
  ngrok http 8000
  # → https://xxxx.ngrok-free.app 형태의 주소가 발급됨
  ```
- **실제 운영**: Railway, Render, Fly.io, AWS, GCP 등에 배포
  - `ANTHROPIC_API_KEY` 등 환경변수를 배포 환경에 등록하세요.

스킬 서버 주소는 `https://<도메인>/skill` 이 됩니다.

---

## 4. 카카오 i 오픈빌더에 스킬 등록

1. [오픈빌더](https://i.kakao.com)에서 봇 선택 → 좌측 **스킬** → **스킬 만들기**
2. **URL** 에 위 주소(`https://<도메인>/skill`) 입력 후 저장
3. 좌측 **시나리오** → 폴백 블록(또는 원하는 블록) 선택
4. **봇 응답** 대신 **스킬 데이터** 를 사용하도록 설정하고, 위에서 만든 스킬을 연결
5. 우측 상단 **배포** 클릭

> 💡 **모든 발화를 Claude로 보내고 싶다면** 폴백 블록(fallback)에 스킬을 연결하는 것이 가장 간단합니다.

### 콜백(Callback) 켜기 — 권장 ⭐

Claude 응답은 5초를 넘길 수 있는데, 카카오 스킬 서버는 기본 5초 안에 응답해야 합니다.
**콜백을 켜면** 서버가 먼저 "대기 메시지"를 보내고, 실제 답변을 1분 이내에 이어서 보낼 수 있습니다.

- 스킬 설정에서 **봇 응답 더보기 → AI 챗봇(콜백) 사용** 을 활성화하세요.
- 콜백이 켜지면 카카오가 요청에 `callbackUrl` 을 함께 보내며, 이 서버가 자동으로 비동기 처리합니다.
- 콜백을 켜지 않아도 동작하지만, 응답이 느린 경우 타임아웃이 날 수 있습니다.

---

## 5. 설정 (.env)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `ANTHROPIC_API_KEY` | (필수) | Anthropic API 키 |
| `CLAUDE_MODEL` | `claude-opus-4-8` | 사용 모델. 속도/비용이 중요하면 `claude-sonnet-4-6` 또는 `claude-haiku-4-5` |
| `MAX_TOKENS` | `2048` | 응답 최대 토큰 (thinking 포함) |
| `ENABLE_THINKING` | `true` | adaptive thinking 사용. `false` 면 더 빠르지만 단순 |
| `SYSTEM_PROMPT` | (기본 페르소나) | 챗봇 성격/지침 |
| `HISTORY_MAX_TURNS` | `6` | 사용자별 기억할 최근 대화 턴 수 |
| `REQUEST_TIMEOUT` | `50` | Claude 응답 대기 최대 시간(초) |

---

## 6. 프로젝트 구조

```
.
├── app/
│   ├── main.py           # FastAPI 엔드포인트 (/skill, /health)
│   ├── config.py         # 환경변수 설정
│   ├── kakao.py          # 카카오 요청/응답 포맷 헬퍼
│   ├── claude_client.py  # Claude API 호출
│   └── conversation.py   # 사용자별 대화 기록 (인메모리)
├── tests/
│   └── test_skill.py     # 서버 동작 테스트
├── requirements.txt
├── .env.example
└── README.md
```

---

## 7. 테스트

```bash
pip install -r requirements.txt
pytest -q
```

---

## 8. 운영 시 참고

- **대화 기록은 메모리에만 저장**됩니다. 서버를 재시작하면 사라지고, 인스턴스를 여러 개로
  늘리면 사용자별 맥락이 일관되지 않습니다. 운영 환경에서는 **Redis** 등 외부 저장소로
  `app/conversation.py` 를 교체하세요.
- API 키 등 비밀값은 `.env` 에 두고 **절대 깃에 커밋하지 마세요** (`.gitignore`에 이미 포함).
- 비용/속도가 중요하면 `CLAUDE_MODEL` 을 `claude-haiku-4-5` 로, `ENABLE_THINKING=false` 로
  바꿔보세요.
