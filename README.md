# 유튜브 자동 요약 워크플로우

유튜브 영상의 자막을 가져와 Claude API로 한국어 요약을 만들어 `summaries/` 에 저장합니다.

## 준비

1. 저장소 Settings → Secrets and variables → Actions 에서 `ANTHROPIC_API_KEY` 를 등록합니다.
2. (로컬 실행 시) `pip install -r requirements.txt`

## 사용법

### GitHub Actions

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
