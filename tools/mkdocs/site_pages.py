"""MkDocs hook: pages that live outside docs/.

- README.md becomes the home page (index.md).
- Every topic file in context/ becomes /context/<name>/ ("Why it is built
  this way", recorded with Keep the Why - https://keepthewhy.com).
- tools/mkdocs/extra.css becomes assets/extra.css (extra_css in mkdocs.yml),
  so the site's styling stays out of docs/.

Both are generated at build time from the files themselves, so there is no
copy under docs/ to keep in sync. A relative link that points at a file the
site does not publish (source code, AGENTS.md, ...) is rewritten to that
file on GitHub, so it keeps working on the site.
"""

from __future__ import annotations

import posixpath
import re
from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_DIR = REPO_ROOT / "context"
EXTRA_CSS = Path(__file__).resolve().parent / "extra.css"
BLOB = "https://github.com/hasansezertasan/copier-pyproject/blob/main/"

# context/ scaffolding, not topic files: the on-disk README and the agent guards.
NOT_PAGES = {"README.md", "AGENTS.md", "CLAUDE.md"}

# site page -> path of its source in the repository
SOURCES: dict[str, str] = {}

LINK = re.compile(r"(\]\()([^)\s#]+)(#[^)\s]*)?(\))")


def on_config(config: MkDocsConfig) -> MkDocsConfig:
    config.watch.extend([str(CONTEXT_DIR), str(REPO_ROOT / "README.md"), str(EXTRA_CSS)])
    return config


def on_files(files: Files, config: MkDocsConfig) -> Files:
    SOURCES.clear()
    readme = REPO_ROOT / "README.md"
    files.append(File.generated(config, "index.md", content=readme.read_text(encoding="utf-8")))
    SOURCES["index.md"] = "README.md"
    files.append(File.generated(config, "assets/extra.css", content=EXTRA_CSS.read_text(encoding="utf-8")))
    for path in sorted(CONTEXT_DIR.glob("*.md")):
        if path.name in NOT_PAGES:
            continue
        uri = f"context/{path.name}"
        files.append(File.generated(config, uri, content=path.read_text(encoding="utf-8")))
        SOURCES[uri] = uri
    return files


def on_page_markdown(markdown: str, page: Page, config: MkDocsConfig, files: Files) -> str:
    src = SOURCES.get(page.file.src_uri, f"docs/{page.file.src_uri}")
    src_dir = posixpath.dirname(src)
    page_dir = posixpath.dirname(page.file.src_uri)

    def fix(m: re.Match) -> str:
        target = m.group(2)
        if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("/"):
            return m.group(0)
        repo_path = posixpath.normpath(posixpath.join(src_dir, target))
        site_uri = repo_path[len("docs/"):] if repo_path.startswith("docs/") else repo_path
        if repo_path == "README.md":
            site_uri = "index.md"
        if files.get_file_from_path(site_uri) is not None:
            rel = posixpath.relpath(site_uri, page_dir or ".")
            return f"{m.group(1)}{rel}{m.group(3) or ''}{m.group(4)}"
        return f"{m.group(1)}{BLOB}{repo_path}{m.group(3) or ''}{m.group(4)}"

    return LINK.sub(fix, markdown)
