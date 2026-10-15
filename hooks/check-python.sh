#!/bin/sh
# Session-start check: the command is a Python 3 script, and Claude Code plugins cannot declare a
# dependency on Python. Silent when Python 3 is there. Never runs python3 itself: on macOS without
# the Command Line Tools, /usr/bin/python3 is a stub whose first run opens Apple's install dialog.
missing=""
p=$(command -v python3 2>/dev/null)
if [ -z "$p" ]; then
  missing=1
elif [ "$p" = /usr/bin/python3 ] && [ "$(uname)" = Darwin ] && ! xcode-select -p >/dev/null 2>&1; then
  missing=1
fi
[ -z "$missing" ] && exit 0
if [ "$(uname)" = Darwin ]; then how='run `xcode-select --install` (or `brew install python`)'
else how='install python3 with your package manager'; fi
msg="obsidian-track-changes-agent needs Python 3, which this machine does not have yet: $how, then start a new session."
printf '{"systemMessage":"%s","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s Until then the obsidian-track-changes-agent command cannot run; tell the user before using it."}}\n' "$msg" "$msg"
