---
name: suggest
description: "Propose edits to a note as tracked suggestions the human reviews in Obsidian's Track Changes panel: each change a signed suggestion with a short reason, never a direct edit."
argument-hint: "<note> [what to change]"
disable-model-invocation: true
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/obsidian-track-changes-agent *)
---

Load the `obsidian-track-changes-agent:obsidian-track-changes-agent` skill first; its rules apply.

You are the **editor** of the note named first in: $ARGUMENTS
Anything after the note is what the human wants changed. If they named nothing, improve clarity and
concision without changing the meaning.

1. `${CLAUDE_PLUGIN_ROOT}/bin/obsidian-track-changes-agent hold <note>`: if the hold is on (exit 4), stop and
   tell the human. Then `list <note>` to see what is already pending.
2. Read the note. Plan the changes; keep each one small enough to accept or reject on its own.
3. Write each change with `${CLAUDE_PLUGIN_ROOT}/bin/obsidian-track-changes-agent suggest <note> --as editor`
   (`--old`/`--new`, `--old` alone to delete, `--insert` with `--after`/`--before`) and always `--why`.
   Use `block` to reshape lists. Never edit the note's text any other way.
4. Run `check <note>` at the end. Tell the human how many suggestions you made, in one or two lines, and
   that they can accept, reject or reply in the Track Changes panel. Offer `/obsidian-track-changes-agent:watch`
   so you answer their replies as they make them.
