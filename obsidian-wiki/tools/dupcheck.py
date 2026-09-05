#!/usr/bin/env python3
"""중복 정보 검사 — 위키 노트끼리 본문이 얼마나 겹치는지 대조합니다.

제목만 보던 기존 검사를 대신합니다. frontmatter, 표, 제목줄, 빈 줄은 빼고
'실제 문장'만 비교해서, 짧은 쪽 기준 겹침 비율이 기준치를 넘으면 보고합니다.
"""
import pathlib, sys, itertools

THRESHOLD = 0.70   # CLAUDE.md §6-3 의 기준: 70%
MIN_LINES = 4      # 문장이 너무 적은 노트는 비교 의미 없음

def sentences(path: pathlib.Path) -> set[str]:
    out, in_fm = set(), False
    for i, raw in enumerate(path.read_text(encoding='utf-8').splitlines()):
        line = raw.strip()
        if line == '---':                      # frontmatter 경계
            in_fm = not in_fm if i == 0 or in_fm else in_fm
            continue
        if in_fm or not line:
            continue
        if line.startswith(('#', '|', '>', '- [ ]', '- [x]', '```')):
            continue
        if len(line) < 25:                     # 너무 짧은 줄은 우연히 겹침
            continue
        out.add(line)
    return out

def main() -> int:
    notes = [p for p in pathlib.Path('wiki').rglob('*.md') if p.name != 'README.md']
    data = {p: sentences(p) for p in notes}
    hits = 0
    for a, b in itertools.combinations(notes, 2):
        sa, sb = data[a], data[b]
        if len(sa) < MIN_LINES or len(sb) < MIN_LINES:
            continue
        shared = sa & sb
        ratio = len(shared) / min(len(sa), len(sb))
        if ratio >= THRESHOLD:
            print(f"  ⚠️  중복 {ratio:.0%} → {a}  ↔  {b}")
            print(f"      겹치는 문장 {len(shared)}줄. 하나로 통합하고 다른 쪽은 링크로 바꾸세요.")
            hits += 1
    if not hits:
        print("  (검출 없으면 통과)")
    return 0

if __name__ == '__main__':
    sys.exit(main())
