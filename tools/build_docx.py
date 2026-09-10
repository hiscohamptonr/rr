"""Build the three January 2026 human-readable DOCX guides.

Markdown under ``docs/`` is the maintained source.
This module assembles reference copies without altering source Markdown.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUTPUT = DOCS / "generated"
BUILDER = Path(__file__).resolve()

# Change this when the assembly/rewriting rules change.  It makes the source
# identity explicit even when the builder hash is not retained by a caller.
BUILDER_SEMANTICS = (
    "docx-source-manifest-v1; stable-heading-anchors-v1; "
    "generated-link-rebase-v1; human-guides-only-v2"
)


@dataclass(frozen=True)
class Document:
    stem: str
    title: str
    pages: tuple[Path, ...]


SHARED_PAGES = (
    DOCS / "operating-controls.md",
)

DOCUMENTS = (
    Document(
        stem="PRA-BSCR-Jan-2026",
        title="PRA and BSCR Runbook",
        pages=(
            DOCS / "pra" / "runbook.md",
            DOCS / "bscr" / "runbook.md",
            *SHARED_PAGES,
        ),
    ),
    Document(
        stem="Lloyds-Supplementary-Jan-2026",
        title="Lloyd's/RDS Supplementary Runbook",
        pages=(
            DOCS / "lloyds" / "runbook.md",
            *SHARED_PAGES,
        ),
    ),
    Document(
        stem="Global-Exposures-Jan-2026",
        title="Global Exposures Runbook",
        pages=(
            DOCS / "global-exposures" / "runbook.md",
            *SHARED_PAGES,
        ),
    ),
)


@dataclass(frozen=True)
class PreparedPage:
    path: Path
    text: str
    prefix: str
    page_anchor: str
    anchors: dict[str, tuple[str, ...]]


_HEADING = re.compile(r"^(?P<marks>#{1,6})\s+(?P<text>.*?)(?:\s+#+)?\s*$")
_FENCE = re.compile(r"^\s*(?P<mark>`{3,}|~{3,})")
_LINK = re.compile(
    r"(?<!!)\[(?P<label>[^\]]+)\]\((?P<target><[^>]*>|[^)\s]+)(?P<tail>[^)]*)\)"
)



def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_hash(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    return raw.decode("utf-8"), _sha256(raw)


def _relative_source(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def _slug(value: str) -> str:
    """Create a conservative, ASCII Pandoc-compatible identifier component."""

    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "section"


def _page_prefix(path: Path) -> str:
    relative = path.resolve().relative_to(DOCS).with_suffix("")
    return "-".join(relative.parts)


def _prepare_page(path: Path) -> PreparedPage:
    text, _ = _source_hash(path)
    prefix = _page_prefix(path)
    counts: dict[str, int] = {}
    aliases: dict[str, list[str]] = {}
    rendered: list[str] = []
    fenced = False
    fence_mark = ""

    for line in text.splitlines():
        fence = _FENCE.match(line)
        if fence:
            marker = fence.group("mark")[0]
            if not fenced:
                fenced = True
                fence_mark = marker
            elif marker == fence_mark:
                fenced = False
            rendered.append(line)
            continue

        heading = None if fenced else _HEADING.match(line)
        if heading:
            heading_text = heading.group("text").strip()
            base = f"{prefix}-{_slug(heading_text)}"
            counts[base] = counts.get(base, 0) + 1
            anchor = base if counts[base] == 1 else f"{base}-{counts[base]}"
            aliases.setdefault(_slug(heading_text), []).append(anchor)
            aliases.setdefault(anchor, []).append(anchor)
            rendered.append(f"{heading.group('marks')} {heading_text} {{#{anchor}}}")
        else:
            rendered.append(line)

    if not aliases:
        # Every current source page has a heading, but retaining a deterministic
        # page anchor makes this helper safe for a future front-matter-only page.
        page_anchor = f"{prefix}-document"
    else:
        page_anchor = next(iter(aliases.values()))[0]

    return PreparedPage(
        path=path.resolve(),
        text="\n".join(rendered),
        prefix=prefix,
        page_anchor=page_anchor,
        anchors={key: tuple(value) for key, value in aliases.items()},
    )


def _anchor_for(page: PreparedPage, fragment: str) -> str | None:
    fragment = unquote(fragment).lstrip("#").casefold()
    if not fragment:
        return page.page_anchor
    exact = page.anchors.get(fragment)
    if exact and len(exact) == 1:
        return exact[0]

    # Existing source links may use Pandoc's unprefixed auto-id, or a stable
    # decision ID such as ``global-01`` that prefixes the full heading slug.
    candidates = {
        anchor
        for alias, anchors in page.anchors.items()
        if alias.startswith(fragment + "-")
        for anchor in anchors
    }
    return next(iter(candidates)) if len(candidates) == 1 else None


def _resolve_target(page: PreparedPage, raw_path: str) -> Path | None:
    candidate = (page.path.parent / unquote(raw_path)).resolve()
    return candidate if candidate.exists() else None


def _generated_relative(path: Path) -> str:
    return Path(os.path.relpath(path, OUTPUT)).as_posix()


def _rewrite_link(
    page: PreparedPage,
    target: str,
    pages: dict[Path, PreparedPage],
) -> str:
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    parsed = urlsplit(target)

    # Keep web, mailto, and other non-file links unchanged.
    if parsed.scheme or parsed.netloc:
        return target

    if not parsed.path:
        anchor = _anchor_for(page, parsed.fragment)
        return f"#{anchor}" if anchor is not None else target

    target_page = _resolve_target(page, parsed.path)
    if target_page is not None and target_page in pages:
        anchor = _anchor_for(pages[target_page], parsed.fragment)
        if anchor is not None:
            return f"#{anchor}"
        # An unresolved fragment is safer as a rebased file link than as a
        # guessed anchor; this keeps the source identity visible to the reader.
        if parsed.fragment:
            return f"{_generated_relative(target_page)}#{parsed.fragment}"
        return f"#{pages[target_page].page_anchor}"

    # Non-included repository resources (including README) are relative to the
    # generated output directory, not the temporary Markdown file or source doc.
    if target_page is None:
        target_page = (page.path.parent / unquote(parsed.path)).resolve()
    rebased = _generated_relative(target_page)
    return f"{rebased}#{parsed.fragment}" if parsed.fragment else rebased


def _rewrite_links(page: PreparedPage, pages: dict[Path, PreparedPage]) -> str:
    fenced = False
    fence_mark = ""
    lines: list[str] = []
    for line in page.text.splitlines():
        fence = _FENCE.match(line)
        if fence:
            marker = fence.group("mark")[0]
            if not fenced:
                fenced = True
                fence_mark = marker
            elif marker == fence_mark:
                fenced = False
            lines.append(line)
            continue
        if fenced:
            lines.append(line)
            continue

        def replace(match: re.Match[str]) -> str:
            new_target = _rewrite_link(page, match.group("target"), pages)
            return f"[{match.group('label')}]({new_target}{match.group('tail')})"

        lines.append(_LINK.sub(replace, line))
    return "\n".join(lines)


def _git_revision() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "unavailable"
    revision = result.stdout.strip()
    return revision if result.returncode == 0 and revision else "unavailable"


def _identity(document: Document, pages: tuple[PreparedPage, ...]) -> tuple[str, str, str]:
    records = []
    for page in pages:
        raw = page.path.read_bytes()
        digest = _sha256(raw)
        records.append(f"{_relative_source(page.path)}\0{digest}".encode("utf-8"))
    manifest = _sha256(b"".join(records))
    builder_digest = _sha256(BUILDER.read_bytes())
    lines = [
        "## Source identity {#source-identity}",
        "",
        f"- Git revision: `{_git_revision()}` (the working tree may contain uncommitted changes).",
        f"- Builder SHA-256: `{builder_digest}`.",
        f"- Assembly semantics: `{BUILDER_SEMANTICS}`.",
        f"- Exact input-doc manifest SHA-256: `{manifest}`.",
        "",
        "The per-file hashes below are computed from the current UTF-8 bytes, so "
        "uncommitted Markdown edits remain distinguishable even when the Git "
        "revision is unchanged:",
        "",
        "| Included source | SHA-256 |",
        "|---|---|",
    ]
    for page in pages:
        lines.append(f"| `{_relative_source(page.path)}` | `{_sha256(page.path.read_bytes())}` |")
    return "\n".join(lines), manifest, builder_digest


def combined_markdown(document: Document) -> str:
    pages = tuple(_prepare_page(page) for page in document.pages)
    page_map = {page.path: page for page in pages}
    identity, _, _ = _identity(document, pages)
    sections = [
        "---",
        f'title: "{document.title}"',
        'subtitle: "January 2026"',
        "---",
        "",
        "> Short operator guide. Detailed technical references are linked, not "
        "included. Markdown is the maintained source; use approved inputs and "
        "templates for the reporting cycle.",
        "",
    ]
    for page in pages:
        sections.extend(
            [
                "",
                '<div class="page-break"></div>',
                "",
                f"<!-- Included source: {_relative_source(page.path)} -->",
                _rewrite_links(page, page_map).strip(),
            ]
        )
    sections.extend(["", identity])
    return "\n".join(sections) + "\n"


def build() -> list[Path]:
    if shutil.which("pandoc") is None:
        raise RuntimeError("pandoc is required to generate DOCX files")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    generated = []
    for document in DOCUMENTS:
        destination = OUTPUT / f"{document.stem}.docx"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", encoding="utf-8"
        ) as source:
            source.write(combined_markdown(document))
            source.flush()
            subprocess.run(
                [
                    "pandoc",
                    source.name,
                    "--from",
                    "markdown+pipe_tables+fenced_code_blocks+yaml_metadata_block+header_attributes",
                    "--output",
                    str(destination),
                ],
                cwd=ROOT,
                check=True,
            )
        generated.append(destination)
    return generated


def main() -> int:
    for path in build():
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
