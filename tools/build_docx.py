"""Build the three January 2026 process DOCX runbooks."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runbooks" / "source"
OUTPUT = ROOT / "runbooks" / "docx"


@dataclass(frozen=True)
class Document:
    stem: str
    title: str
    pages: tuple[Path, ...]


CONTROLS = SOURCE / "run-checks.md"
DOCUMENTS = (
    Document(
        stem="PRA-BSCR-Jan-2026",
        title="PRA and BSCR Runbook",
        pages=(SOURCE / "pra-bscr.md", SOURCE / "pra.md", SOURCE / "bscr.md", CONTROLS),
    ),
    Document(
        stem="Lloyds-Supplementary-Jan-2026",
        title="Lloyd's/RDS Supplementary Runbook",
        pages=(SOURCE / "lloyds-supplementary.md", CONTROLS),
    ),
    Document(
        stem="Global-Exposures-Jan-2026",
        title="Global Exposures Runbook",
        pages=(SOURCE / "global-exposures.md", CONTROLS),
    ),
)


def combined_markdown(document: Document) -> str:
    sections = [
        "---",
        f'title: "{document.title}"',
        'subtitle: "January 2026"',
        "---",
        "",
        "> Current approved instructions, templates, databases, mappings, and rates remain authoritative.",
    ]
    for page in document.pages:
        sections.extend(
            [
                "",
                '<div class="page-break"></div>',
                "",
                page.read_text(encoding="utf-8").strip(),
            ]
        )
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
                    "gfm+yaml_metadata_block",
                    "--toc",
                    "--number-sections",
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
