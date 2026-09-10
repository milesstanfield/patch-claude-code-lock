# patch-claude-code-lock

Scripts that patch the Claude Code (`anthropic.claude-code`) VS Code/Cursor extension's minified `extension.js` to fix editor-group locking and change where new sessions open.

## What it fixes

There is no setting for any of this — the only fix is patching the obfuscated `extension.js` on the local machine:

- [anthropics/claude-code#80148](https://github.com/anthropics/claude-code/issues/80148) — extension programmatically locks the editor group (`workbench.action.lockEditorGroup`), bypassing `workbench.editor.autoLockGroups`
- [anthropics/claude-code#83333](https://github.com/anthropics/claude-code/issues/83333) — `findUnusedColumn()` creates an empty editor group (blank pane with only an X) when opening beside Cursor Agents

`scripts/patch.py` applies two fixes:

1. **Lock**: neutralizes the `workbench.action.lockEditorGroup` call, so the group Claude Code opens into is never locked.
2. **Column**: replaces the `findUnusedColumn()` / `ViewColumn.Beside` fallback (used when no Claude Code panel is already open) with `ViewColumn.Active`, so **"+ New session" opens as a new tab in your current active editor group** instead of splitting into a new column beside it.

Note the column fix is a deliberate behavior change, not just a bugfix — by default Claude Code opens beside your current group (which is what #83333's stray-empty-column bug was about); this patch goes further and stops it from opening a separate column at all.

Extension updates install into a fresh directory, so re-run the patch after every update.

## Usage

Clone this repo, then from its directory:

```bash
python3 scripts/patch.py
```

This finds every `anthropic.claude-code-*` install under `~/.cursor/extensions` and `~/.vscode/extensions` and applies both fixes to each `extension.js`. Already-patched pieces are skipped. Before its first write to a given `extension.js`, it's backed up to `extension.js.bak` (never overwritten once it exists), and the script's output tells you where the backup is and how to restore it.

After a successful patch, reload the window (`Developer: Reload Window`), close any leftover empty group once, and unlock any already-locked group once (the patch only prevents future locks/empty columns).

### Reverting

```bash
python3 scripts/restore.py
```

Restores `extension.js` from `extension.js.bak` for every install where a backup exists, undoing both patches. Reload the window afterward.

## Supported versions

Verified lock + column patch against:

| Host | Versions |
| --- | --- |
| VS Code | `2.1.216`, `2.1.241`, `2.1.243`, `2.1.245`–`2.1.247`, `2.1.250`–`2.1.252`, `2.1.267` |
| Cursor | `2.1.238`, `2.1.239`, `2.1.263`, `2.1.266` |

The matcher treats minified locals as identifiers, not literals, so it covers both the 2.1.216 call site (`n=!0}let o=`) and later sites (`i=!0}let s=` and similar). Detected vscode aliases so far: `Nt` / `Lt` (2.1.238–239), `O4` (2.1.263), `B4` (2.1.266–267). Re-run after every extension update; if a later build reports `PATTERN NOT FOUND`, the bundle changed again.

## License

[MIT](LICENSE)
