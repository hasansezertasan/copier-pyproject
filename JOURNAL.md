# Development Journal

Chronological record of decisions, attempts (including failures), and outcomes.

---

## 2026-02-01 — Initial Codebase Analysis and Documentation Setup

### Context

Performed a comprehensive analysis of the copier-pyproject template to understand the full scope of the project and establish documentation practices.

### Findings

- The template generates modern Python packages with 30+ configurable options
- Supports 7 optional components: CLI (Typer), Web (FastAPI/Litestar), GUI (Tkinter), TUI (Textual), MCP server, Worker (FastStream), C Extensions (Cython)
- Includes 13 linting/formatting tools, 99% coverage requirement, and multi-platform CI
- CD workflow supports PyPI trusted publishing, Docker Hub + GHCR, PyCrucible executables
- 130 template files using Jinja2 with conditional file inclusion

### Alternatives Researched

| Tool                 | Pros                                                 | Cons                                     |
| -------------------- | ---------------------------------------------------- | ---------------------------------------- |
| **Cookiecutter**     | Largest ecosystem, most community templates          | No native update support, feels dated    |
| **Cruft**            | Adds update to Cookiecutter, backward compatible     | Wrapper limitations, not native          |
| **Copier** (chosen)  | Native updates, conditional file paths, answer files | Smaller ecosystem                        |
| **Yeoman**           | Mature, multi-language                               | JavaScript-based, not Python-native      |
| **GitHub Templates** | Zero tooling needed                                  | No variable substitution or conditionals |

### Actions Taken

- Created Architecture Decision Record (ADR-001): Copier over Cookiecutter
- Created this JOURNAL.md for ongoing development tracking

### Current State (feat/packaging-and-deploy branch)

Recent work has focused on:

- Worker and FastStream message queue integration (Kafka, NATS, RabbitMQ, Redis)
- Docker publishing to both Docker Hub and GHCR
- Devcontainer consolidation with optional services
- CD workflow enhancements (PyCrucible, multi-arch Docker)
