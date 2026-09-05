"""YouTube 영상 자막을 가져와 Claude로 요약한다."""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
)

MODEL = "claude-sonnet-5"
DEFAULT_LANGS = ["ko", "en"]

PROMPT = """다음은 유튜브 영상 「{title}」의 자막 전문입니다.

<transcript>
{transcript}
</transcript>

아래 형식의 한국어 마크다운으로 요약해 주세요.

## 한 줄 요약
(영상 전체를 한 문장으로)

## 핵심 포인트
- 5~8개의 불릿. 각 불릿은 한 문장.

## 상세 요약
문단 3~5개. 영상의 흐름을 따라가며 정리.

## 인상적인 문장
자막에서 그대로 인용한 문장 2~3개.

## 다음 행동 / 시사점
- 시청자가 실제로 활용할 수 있는 것 위주로 2~4개.

자막에 없는 내용은 지어내지 마세요."""


def load_env_file(path: Path = Path(".env")) -> None:
    """.env 파일이 있으면 KEY=VALUE 를 환경변수로 읽어들인다."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def extract_video_id(url_or_id: str) -> str:
    """URL 또는 ID 문자열에서 11자리 영상 ID를 뽑는다."""
    if re.fullmatch(r"[\w-]{11}", url_or_id):
        return url_or_id

    patterns = [
        r"(?:youtube\.com/watch\?(?:.*&)?v=)([\w-]{11})",
        r"(?:youtu\.be/)([\w-]{11})",
        r"(?:youtube\.com/(?:embed|shorts|live)/)([\w-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    raise ValueError(f"영상 ID를 찾을 수 없습니다: {url_or_id}")


def fetch_video_title(video_id: str) -> str | None:
    """영상 제목을 가져온다(옵시디언 노트 이름용). 실패하면 None."""
    try:
        response = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
        title = response.json().get("title", "").strip()
        return title or None
    except (requests.RequestException, ValueError):
        return None


def fetch_transcript(video_id: str, languages: list[str]) -> str:
    """수동 자막을 우선 쓰고, 없으면 자동 생성 자막으로 넘어간다."""
    api = YouTubeTranscriptApi()
    try:
        transcript_list = api.list(video_id)
    except RequestBlocked as exc:
        raise RuntimeError(
            "유튜브가 현재 IP를 차단했습니다. 클라우드 서버가 아닌 개인 PC에서 실행하거나, "
            "잠시 후 다시 시도해 주세요."
        ) from exc
    except (TranscriptsDisabled, VideoUnavailable) as exc:
        raise RuntimeError(f"자막을 가져올 수 없습니다 ({video_id}): {exc}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(
            f"유튜브에 연결하지 못했습니다. 인터넷 연결을 확인해 주세요.\n({exc.__class__.__name__})"
        ) from exc

    try:
        transcript = transcript_list.find_manually_created_transcript(languages)
    except NoTranscriptFound:
        try:
            transcript = transcript_list.find_generated_transcript(languages)
        except NoTranscriptFound as exc:
            available = ", ".join(t.language_code for t in transcript_list) or "없음"
            raise RuntimeError(
                f"{languages} 자막이 없습니다. 사용 가능한 언어: {available}"
            ) from exc

    return " ".join(snippet.text.strip() for snippet in transcript.fetch())


def summarize(transcript: str, title: str) -> str:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": PROMPT.format(title=title, transcript=transcript),
            }
        ],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def write_summary(out_dir: Path, video_id: str, url: str, body: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = out_dir / f"{stamp}-{video_id}.md"
    path.write_text(
        f"# 요약: {url}\n\n"
        f"- 영상: {url}\n"
        f"- 생성: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n"
        f"{body}\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="유튜브 영상 자동 요약")
    parser.add_argument("url", help="유튜브 URL 또는 영상 ID")
    parser.add_argument(
        "--lang",
        default=",".join(DEFAULT_LANGS),
        help="자막 언어 우선순위 (쉼표 구분, 기본: ko,en)",
    )
    parser.add_argument(
        "--out-dir", default="summaries", type=Path, help="요약 저장 디렉터리"
    )
    parser.add_argument(
        "--stdout", action="store_true", help="파일로 저장하지 않고 화면에만 출력"
    )
    parser.add_argument(
        "--obsidian",
        action="store_true",
        help="옵시디언 볼트에도 노트로 저장 (.env 의 OBSIDIAN_VAULT 사용)",
    )
    parser.add_argument(
        "--obsidian-folder",
        default="유튜브 요약",
        help="옵시디언 볼트 안의 저장 폴더 (기본: 유튜브 요약)",
    )
    args = parser.parse_args()

    load_env_file()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY 가 없습니다.\n"
            ".env.example 을 복사해 .env 파일을 만들고 API 키를 넣어주세요.",
            file=sys.stderr,
        )
        return 2

    try:
        video_id = extract_video_id(args.url)
        languages = [lang.strip() for lang in args.lang.split(",") if lang.strip()]
        transcript = fetch_transcript(video_id, languages)
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    url = f"https://www.youtube.com/watch?v={video_id}"
    body = summarize(transcript, url)

    if args.stdout:
        print(body)
        return 0

    path = write_summary(args.out_dir, video_id, url, body)
    print(f"저장 완료: {path}")

    if args.obsidian:
        from obsidian_save import save_note

        title = fetch_video_title(video_id) or f"유튜브 요약 {video_id}"
        try:
            note_path = save_note(
                body=body,
                title=title,
                folder=args.obsidian_folder,
                tags=["유튜브", "요약"],
                source=url,
                date_prefix=True,
            )
            print(f"옵시디언 저장 완료: {note_path}")
        except (RuntimeError, ValueError) as exc:
            print(f"옵시디언 저장 실패: {exc}", file=sys.stderr)

    if step_summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        Path(step_summary).write_text(body, encoding="utf-8")
    if github_output := os.environ.get("GITHUB_OUTPUT"):
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write(f"summary_path={path}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
