"""옵시디언(Obsidian) 볼트에 마크다운 노트를 저장한다.

옵시디언 볼트는 특별한 데이터베이스가 아니라 그냥 `.md` 파일이 들어 있는 폴더다.
그래서 저장은 "정해진 폴더에 마크다운 파일을 쓰는 것"이 전부다.

이 파일은 일부러 표준 라이브러리만 쓴다. pip 설치 없이 단독 실행할 수 있어야
요약 기능과 상관없이 어디서든 노트를 저장할 수 있기 때문이다.

사용 예:
    python src/obsidian_save.py --title "제목" --folder "유튜브 요약" \
        --tags 유튜브,요약 --source "https://youtu.be/..." < 본문.md
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# 옵시디언과 윈도우에서 파일 이름에 쓸 수 없는 글자.
# #, ^, [, ] 는 파일 이름에는 들어가지만 [[내부링크]]를 깨뜨려서 같이 지운다.
FORBIDDEN_FILENAME_CHARS = r'[\\/:*?"<>|#^\[\]]'

# 파일 이름 최대 길이(바이트). 대부분의 파일 시스템 한계가 255바이트라서
# 날짜 접두사와 ".md" 를 붙일 여유를 두고 잡았다.
MAX_FILENAME_BYTES = 150


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


def resolve_vault(explicit: str | None = None) -> Path:
    """볼트 폴더를 찾는다. --vault 인자 > OBSIDIAN_VAULT 환경변수 순서."""
    raw = explicit or os.environ.get("OBSIDIAN_VAULT", "")
    raw = raw.strip().strip("'\"")
    if not raw:
        raise RuntimeError(
            "옵시디언 볼트 경로를 모르겠습니다.\n"
            "  .env 파일에 OBSIDIAN_VAULT=볼트폴더경로 를 넣거나\n"
            "  --vault \"볼트폴더경로\" 로 직접 알려주세요.\n"
            "  (볼트 폴더 = 옵시디언에서 열어 둔 그 폴더. 안에 .obsidian 폴더가 있습니다.)"
        )

    vault = Path(raw).expanduser()
    if not vault.is_dir():
        raise RuntimeError(f"볼트 폴더가 없습니다: {vault}")
    return vault.resolve()


def _truncate_bytes(text: str, limit: int) -> str:
    """UTF-8 기준 limit 바이트를 넘지 않게 자른다(글자 중간에서 끊기지 않게)."""
    encoded = text.encode("utf-8")
    if len(encoded) <= limit:
        return text
    return encoded[:limit].decode("utf-8", errors="ignore").rstrip()


def sanitize_filename(name: str) -> str:
    """제목을 파일 이름으로 쓸 수 있게 다듬는다."""
    cleaned = re.sub(FORBIDDEN_FILENAME_CHARS, " ", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    cleaned = _truncate_bytes(cleaned, MAX_FILENAME_BYTES)
    if not cleaned:
        raise ValueError(f"파일 이름으로 쓸 수 있는 글자가 없습니다: {name!r}")
    return cleaned


def normalize_tag(tag: str) -> str:
    """옵시디언 태그 규칙에 맞게 다듬는다(공백 불가, 앞의 # 제거)."""
    tag = tag.strip().lstrip("#").strip()
    tag = re.sub(r"\s+", "-", tag)
    return re.sub(r"[^\w/\-가-힣]", "", tag)


def _yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def strip_existing_frontmatter(body: str) -> tuple[str, bool]:
    """본문이 이미 --- 속성 블록으로 시작하면 떼어낸다(속성 블록 중복 방지)."""
    if not body.startswith("---\n"):
        return body, False
    end = body.find("\n---", 4)
    if end == -1:
        return body, False
    return body[end + 4 :].lstrip("\n"), True


def build_frontmatter(
    title: str,
    tags: list[str],
    source: str | None = None,
    extra: dict[str, str] | None = None,
) -> str:
    """옵시디언 속성(프로퍼티) 블록을 만든다."""
    lines = ["---", f"title: {_yaml_quote(title)}"]
    lines.append(f"created: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")
    if tags:
        lines.append("tags:")
        lines.extend(f"  - {tag}" for tag in tags)
    if source:
        lines.append(f"source: {_yaml_quote(source)}")
    for key, value in (extra or {}).items():
        lines.append(f"{key}: {_yaml_quote(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def _unique_path(path: Path) -> Path:
    """같은 이름이 있으면 뒤에 2, 3... 을 붙인다."""
    if not path.exists():
        return path
    for number in range(2, 1000):
        candidate = path.with_name(f"{path.stem} {number}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"이름이 겹치는 파일이 너무 많습니다: {path}")


def target_path(
    vault: Path,
    title: str,
    folder: str = "",
    filename: str | None = None,
    date_prefix: bool = False,
) -> Path:
    """볼트 안의 저장 위치를 계산한다(볼트 밖으로 나가지 못하게 막는다)."""
    stem = sanitize_filename(filename or title)
    if date_prefix:
        stem = f"{datetime.now().strftime('%Y-%m-%d')} {stem}"

    directory = vault
    for part in Path(folder.replace("\\", "/")).parts if folder else ():
        if part in ("..", "/", "."):
            raise ValueError(f"폴더 이름에 쓸 수 없는 값입니다: {folder!r}")
        directory = directory / sanitize_filename(part)

    path = directory / f"{stem}.md"
    if not path.resolve().parent.is_relative_to(vault):
        raise ValueError(f"볼트 바깥에는 저장할 수 없습니다: {path}")
    return path


def save_note(
    body: str,
    title: str,
    vault: Path | str | None = None,
    folder: str = "",
    tags: list[str] | None = None,
    source: str | None = None,
    filename: str | None = None,
    mode: str = "new",
    date_prefix: bool = False,
    frontmatter: bool = True,
    extra: dict[str, str] | None = None,
    dry_run: bool = False,
) -> Path:
    """볼트에 노트 하나를 저장하고 저장된 경로를 돌려준다.

    mode: new(겹치면 새 이름) / overwrite(덮어쓰기) / append(기존 파일 뒤에 붙이기)
    """
    if mode not in ("new", "overwrite", "append"):
        raise ValueError(f"mode 는 new, overwrite, append 중 하나여야 합니다: {mode}")

    vault_path = vault if isinstance(vault, Path) else resolve_vault(vault)
    path = target_path(vault_path, title, folder, filename, date_prefix)

    body = body.strip()
    if not body:
        raise ValueError("저장할 본문이 비어 있습니다.")

    stripped, had_frontmatter = strip_existing_frontmatter(body)
    if had_frontmatter and frontmatter:
        print("본문 앞에 있던 속성(---) 블록은 새로 만든 것으로 바꿨습니다.", file=sys.stderr)
        body = stripped

    if mode == "append" and path.exists():
        content = path.read_text(encoding="utf-8").rstrip() + "\n\n---\n\n" + body + "\n"
    else:
        if mode == "new":
            path = _unique_path(path)
        head = ""
        if frontmatter:
            head = build_frontmatter(
                title, [normalize_tag(t) for t in (tags or []) if normalize_tag(t)],
                source, extra,
            )
        content = head + body + "\n"

    if dry_run:
        print(f"[미리보기] 저장할 위치: {path}", file=sys.stderr)
        print(content)
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="옵시디언 볼트에 마크다운 노트 저장")
    parser.add_argument("--title", required=True, help="노트 제목(파일 이름이 된다)")
    parser.add_argument("--folder", default="", help="볼트 안의 하위 폴더 (예: '유튜브 요약')")
    parser.add_argument("--tags", default="", help="태그 (쉼표 구분, 예: 유튜브,요약)")
    parser.add_argument("--source", default="", help="출처 링크")
    parser.add_argument("--vault", default="", help="볼트 폴더 경로 (기본: OBSIDIAN_VAULT)")
    parser.add_argument("--file", type=Path, help="본문이 들어 있는 파일 (기본: 표준입력)")
    parser.add_argument("--filename", help="파일 이름을 제목과 다르게 쓰고 싶을 때")
    parser.add_argument(
        "--mode",
        default="new",
        choices=["new", "overwrite", "append"],
        help="이름이 겹칠 때: new=새 이름, overwrite=덮어쓰기, append=뒤에 붙이기",
    )
    parser.add_argument("--date-prefix", action="store_true", help="파일 이름 앞에 날짜 붙이기")
    parser.add_argument("--no-frontmatter", action="store_true", help="속성(---) 블록 없이 저장")
    parser.add_argument("--dry-run", action="store_true", help="저장하지 않고 결과만 보여주기")
    args = parser.parse_args()

    load_env_file()

    body = args.file.read_text(encoding="utf-8") if args.file else sys.stdin.read()

    try:
        path = save_note(
            body=body,
            title=args.title,
            vault=args.vault or None,
            folder=args.folder,
            tags=[t for t in args.tags.split(",") if t.strip()],
            source=args.source or None,
            filename=args.filename,
            mode=args.mode,
            date_prefix=args.date_prefix,
            frontmatter=not args.no_frontmatter,
            dry_run=args.dry_run,
        )
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not args.dry_run:
        print(f"저장 완료: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
