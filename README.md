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

## 옵시디언(Obsidian) 저장

요약이나 대본을 옵시디언 볼트에 마크다운 노트로 바로 저장할 수 있습니다.
옵시디언 볼트는 `.md` 파일이 들어 있는 그냥 폴더라서, 파일만 써 넣으면 앱에 바로 나타납니다.

먼저 `.env` 에 볼트 폴더 경로를 넣습니다.

```
OBSIDIAN_VAULT=C:\Users\내이름\Documents\내볼트
```

**유튜브 요약을 저장할 때** — `--obsidian` 을 붙입니다.

```bash
python src/summarize.py "https://youtu.be/VIDEO_ID" --obsidian
python src/summarize.py "https://youtu.be/VIDEO_ID" --obsidian --obsidian-folder "쇼츠 소재"
```

**아무 내용이나 저장할 때** — `src/obsidian_save.py` 를 씁니다. (파이썬 표준 기능만 쓰므로
`pip install` 없이도 동작합니다.)

```bash
python src/obsidian_save.py --title "노트 제목" --folder "쇼츠 대본" \
  --tags "쇼츠,대본" --file 내용.md
```

| 옵션 | 설명 |
| --- | --- |
| `--title` | 노트 제목 (파일 이름이 됩니다) |
| `--folder` | 볼트 안 하위 폴더. 없으면 자동 생성 |
| `--tags` | 태그, 쉼표 구분 |
| `--source` | 출처 링크 |
| `--date-prefix` | 파일 이름 앞에 날짜 붙이기 |
| `--mode` | 이름이 겹칠 때 `new`(기본) / `overwrite` / `append` |
| `--dry-run` | 저장하지 않고 결과만 확인 |

볼트 경로는 한 번만 등록해 두면 어느 폴더에서 실행하든 찾아 씁니다.

```bash
python src/obsidian_save.py --set-vault "C:\Users\내이름\Documents\내볼트"
```

찾는 순서는 `--vault` → `OBSIDIAN_VAULT`(환경변수·`.env`) → `~/.claude/obsidian_vault.txt` 입니다.

## Claude Code 스킬

| 스킬 | 트리거 | 하는 일 |
| --- | --- | --- |
| `obsidian-save` | "옵시디언에 저장해줘", "볼트에 저장" | 아무 결과물이나 볼트에 노트로 저장 |
| `vibe-coding-save` | **"5번"**, "5번으로 실행" | 바이브코딩으로 사이트 만든 작업 내용을 학습 노트로 저장 |

**5번 스킬**은 홈페이지를 만든 뒤 그날 한 일을 노트 한 장으로 정리해 볼트의
`바이브코딩 학습` 폴더에 넣습니다. 담기는 것: 한 줄 요약 / 오늘 만든 것 / 파일 구조 /
핵심 코드 / 막혔던 것과 해결법 / 배운 것 / 다음에 할 일.

홈페이지 작업 폴더 등 **다른 폴더에서도 쓰려면 스킬을 설치**해야 합니다.

- 윈도우: `스킬설치.bat` 더블클릭
- 맥: `스킬설치.command` 더블클릭

스킬을 `~/.claude/skills/` 로 복사하고 볼트 경로까지 한 번에 등록합니다.

> **볼트는 내 PC에 있는 폴더**라서 클라우드(웹) 세션에서는 저장되지 않습니다.
> 내 PC의 Claude Code 에서 실행하세요.

## 요약 형식

한 줄 요약 / 핵심 포인트 / 상세 요약 / 인상적인 문장 / 다음 행동. 형식을 바꾸려면
`src/summarize.py` 의 `PROMPT` 상수를 수정하세요.

## 제약

- 자막이 없거나 비활성화된 영상은 요약할 수 없습니다.
- GitHub Actions 러너 IP가 유튜브에서 차단되면 자막 요청이 실패할 수 있습니다.
  이 경우 로컬에서 실행하거나 프록시를 사용하세요.
