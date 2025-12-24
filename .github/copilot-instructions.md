# GitHub Copilot Instructions

## Context
- **Role**: Python/Terminal Developer
- **Focus**: Automation, CLI Tools, HTML Reports
- **OS**: Linux (primary), macOS (secondary), WSL (rare)

## Code Guidelines

### 🐍 Python (3.10+)
- **Tools**: `uv` (deps), `ruff` (lint/fmt), `pytest`
- **Typing**: Strict usage (`list[str]`, `str | None`, `dict[str, Any]`)
- **Paths**: `pathlib.Path` ONLY. No `os.path.join`.
- **Style**: Google docstrings. 88 char limit. Double quotes.

```python
# ✅ DO
def load_config(path: Path) -> dict[str, Any]:
    """Load JSON config."""
    return json.loads(path.read_text())

# ❌ DON'T
def load_config(path): 
    f = open(path) # missing context manager, typing
    return json.load(f)
```

### 📊 HTML Reports
- **Templates**: Use **Jinja2**. Avoid generating HTML strings in code.
- **Self-Contained**: Embed resources (CSS/Images) via base64/inline styles.
- **Data**: Pandas `DataFrame.to_html()` with simple CSS classes.

```python
# Jinja2 Setup Pattern
template = env.get_template("report.html")
html = template.render(
    data=df.to_dict(orient="records"),
    generated_at=datetime.now()
)
```

### 🖥️ Terminal/CLI
- **Framework**: `typer` > `argparse`.
- **Output**: `rich` for colors/tables/progress bars.
- **Fallback**: If standard terminal fails (ENOPRO), use `terminal_session.ipynb` with `!command`. Clear regularly.

```python
import typer
from rich import print

def main(name: str):
    print(f"[bold blue]Processing:[/bold blue] {name}")
```

### 🐚 Shell Scripts
- **Shebang**: `#!/bin/bash`
- **Safety**: `set -euo pipefail` (REQUIRED)
- **OS Check**: `[[ "$OSTYPE" == "darwin"* ]]` vs `linux-gnu`

### 🔒 Security
- **Secrets**: Use `.env` files (`python-dotenv`).
- **Git**: Never commit `.env` or credentials.

### 🧪 Testing
- **Framework**: `pytest`
- **Pattern**: Fixtures over setup/teardown methods.
- **Mocks**: Use `unittest.mock` or `pytest-mock`.
