#!/usr/bin/env python3
"""Patch Claude Code extension.js to stop locking editor groups and to open
new sessions in the active editor group instead of a new column.

Two fixes, both applied to every anthropic.claude-code-* install under
~/.cursor/extensions and ~/.vscode/extensions:

1. Lock: neutralize `workbench.action.lockEditorGroup` when the panel opens
   (`if(X)` -> `if(X&&!1)`).
2. Column: replace the `findUnusedColumn()` / `ViewColumn.Beside` fallback
   used when no Claude Code panel is already open with
   `{alias}.ViewColumn.Active||1`, so "+ New session" lands as a new tab in
   whatever editor group is currently active instead of splitting a new
   column beside it. The minified vscode import alias varies by version
   (e.g. Tt, It, Rt, Nt, Lt, B4) and is detected from the createWebviewPanel
   call that follows.

Before the first write to a given extension.js, it is backed up to
extension.js.bak (never overwritten once it exists), so a patch can be
undone with `python3 scripts/restore.py` (or manually:
`cp extension.js.bak extension.js`).
"""

import re
import shutil
import sys
from pathlib import Path

EXTENSION_ROOTS = [
    Path.home() / ".cursor" / "extensions",
    Path.home() / ".vscode" / "extensions",
]

# Matches: if(E)await Pe.commands.executeCommand("workbench.action.lockEditorGroup")
LOCK_CALL = re.compile(
    r"if\((?P<cond>[A-Za-z$_][\w$]*)\)"
    r'(?P<call>await [A-Za-z$_][\w$]*\.commands\.executeCommand\("workbench\.action\.lockEditorGroup"\))'
)

LOCK_ALREADY = re.compile(
    r"if\([A-Za-z$_][\w$]*&&!1\)"
    r'await [A-Za-z$_][\w$]*\.commands\.executeCommand\("workbench\.action\.lockEditorGroup"\)'
)

# Matches the raw `this.findUnusedColumn()` call, the old
# `{alias}.ViewColumn.Beside||1` form, or the already-patched
# `{alias}.ViewColumn.Active||1` form -- anchored to the createWebviewPanel
# call that follows so the alias is read from a live reference rather than
# guessed from the matched text itself.
COLUMN_SITE = re.compile(
    r"(?:this\.findUnusedColumn\(\)"
    r"|[A-Za-z$_][\w$]*\.ViewColumn\.Beside\|\|1"
    r"|[A-Za-z$_][\w$]*\.ViewColumn\.Active\|\|1)"
    r"(?P<tail>,[A-Za-z$_][\w$]*=!0\}let [A-Za-z$_][\w$]*="
    r"(?P<alias>[A-Za-z$_][\w$]*)\.window\.createWebviewPanel)"
)


def backup(extension_js: Path) -> Path:
    bak = extension_js.with_suffix(extension_js.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(extension_js, bak)
    return bak


def patch_lock(src: str, parts: list[str]) -> str:
    if LOCK_ALREADY.search(src):
        parts.append("lock already patched")
        return src
    patched, count = LOCK_CALL.subn(r"if(\g<cond>&&!1)\g<call>", src)
    if count == 0:
        parts.append("lock PATTERN NOT FOUND")
        return src
    parts.append(f"lock patched ({count})")
    return patched


def patch_column(src: str, parts: list[str]) -> str:
    m = COLUMN_SITE.search(src)
    if m is None:
        parts.append("column PATTERN NOT FOUND")
        return src

    alias = m.group("alias")
    current = m.group(0)[: -len(m.group("tail"))]
    desired = f"{alias}.ViewColumn.Active||1"

    if current == desired:
        parts.append("column already patched")
        return src
    if len(current) != len(desired):
        parts.append(f"column PATTERN NOT FOUND (alias {alias!r} wrong length)")
        return src

    start = m.start()
    parts.append(f"column patched ({alias}, was {current!r})")
    return src[:start] + desired + src[start + len(current) :]


def patch_file(extension_js: Path) -> str:
    src = extension_js.read_text()
    original = src
    parts: list[str] = []

    src = patch_lock(src, parts)
    src = patch_column(src, parts)

    if src != original:
        bak = backup(extension_js)
        extension_js.write_text(src)
        parts.append(f"backup at {bak} (restore with: python3 scripts/restore.py)")

    return "; ".join(parts)


def main() -> int:
    found_any = False
    failures = 0
    for root in EXTENSION_ROOTS:
        if not root.is_dir():
            continue
        for ext_dir in sorted(root.glob("anthropic.claude-code-*")):
            extension_js = ext_dir / "extension.js"
            if not extension_js.is_file():
                print(f"{ext_dir.name}: extension.js missing, skipped")
                continue
            found_any = True
            result = patch_file(extension_js)
            print(f"{ext_dir.name} ({root}): {result}")
            if "NOT FOUND" in result:
                failures += 1
    if not found_any:
        print("No anthropic.claude-code-* extension installations found.")
        return 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
