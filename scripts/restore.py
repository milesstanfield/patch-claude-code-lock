#!/usr/bin/env python3
"""Undo patch.py: restore extension.js from its extension.js.bak backup.

Looks under every anthropic.claude-code-* install in ~/.cursor/extensions
and ~/.vscode/extensions for an extension.js.bak next to extension.js, and
copies it back over extension.js if found. Reload the window afterward for
the restored file to take effect.
"""

import shutil
import sys
from pathlib import Path

EXTENSION_ROOTS = [
    Path.home() / ".cursor" / "extensions",
    Path.home() / ".vscode" / "extensions",
]


def restore_file(extension_js: Path) -> str:
    bak = extension_js.with_suffix(extension_js.suffix + ".bak")
    if not bak.is_file():
        return "no backup found, nothing to restore"
    shutil.copy2(bak, extension_js)
    return f"restored from {bak}"


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
            result = restore_file(extension_js)
            print(f"{ext_dir.name} ({root}): {result}")
            if "no backup found" in result:
                failures += 1
    if not found_any:
        print("No anthropic.claude-code-* extension installations found.")
        return 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
