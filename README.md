# 유튜브 자동 요약 워크플로우

유튜브 영상의 자막을 가져와 Claude API로 한국어 요약을 만들어 `summaries/` 에 저장합니다.

> **처음 쓰시는 분은 [사용설명서.md](사용설명서.md) 를 보세요.** 설치부터 실행까지 그림 없이 따라 할 수 있게 정리돼 있습니다.

## 권장 실행 방법: 내 PC

유튜브가 GitHub Actions 등 클라우드 서버의 IP를 차단하기 때문에, **자동 실행은 실패합니다**
(`RequestBlocked`). 개인 PC에서 실행하세요.

- 윈도우: `실행하기.bat` 더블클릭
- 맥: `실행하기.command` 더블클릭

API 키는 `.env` 파일에 넣습니다 (`.env.example` 참고).

## 준비

1. 저장소 Settings → Secrets and variables → Actions 에서 `ANTHROPIC_API_KEY` 를 등록합니다.
2. (로컬 실행 시) `pip install -r requirements.txt`

## 사용법

### GitHub Actions (참고 — 현재 IP 차단으로 실패함)

유료 프록시를 연결하지 않는 한 클라우드에서는 자막을 가져올 수 없습니다. 아래는 프록시를
붙였을 때를 위한 설명입니다.

Actions 탭 → **YouTube 자동 요약** → *Run workflow* 에서 URL을 입력합니다.

| 입력 | 설명 | 기본값 |
| --- | --- | --- |
| `url` | 유튜브 URL 또는 11자리 영상 ID | (필수) |
| `lang` | 자막 언어 우선순위 | `ko,en` |
| `commit` | 결과를 저장소에 커밋 | `true` |

요약은 실행 요약(Job Summary)에도 함께 표시됩니다.

### 로컬

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python src/summarize.py "https://youtu.be/VIDEO_ID"        # summaries/ 에 저장
python src/summarize.py "https://youtu.be/VIDEO_ID" --stdout  # 화면에만 출력
python src/summarize.py VIDEO_ID --lang ja,en
```

## 요약 형식

한 줄 요약 / 핵심 포인트 / 상세 요약 / 인상적인 문장 / 다음 행동. 형식을 바꾸려면
`src/summarize.py` 의 `PROMPT` 상수를 수정하세요.

## 제약

- 자막이 없거나 비활성화된 영상은 요약할 수 없습니다.
- GitHub Actions 러너 IP가 유튜브에서 차단되면 자막 요청이 실패할 수 있습니다.
  이 경우 로컬에서 실행하거나 프록시를 사용하세요.
