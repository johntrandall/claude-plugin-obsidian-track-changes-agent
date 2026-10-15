---
name: watch
description: "Watch a note (or folder) for the human's Track Changes marks and answer each as it arrives: reply to comments, propose requested changes, accept their comment-free suggestions. Runs until the human says stop."
argument-hint: "<note or folder> [more notes…]"
disable-model-invocation: true
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/obsidian-track-changes-agent *)
---

Load the `obsidian-track-changes-agent:obsidian-track-changes-agent` skill first; its rules apply. You are
the **editor** of the watched notes.

Watch: $ARGUMENTS

1. Arm the watch **in the background** (so the human can keep talking to you):
   `${CLAUDE_PLUGIN_ROOT}/bin/obsidian-track-changes-agent watch <paths…>`
   Tell the human, in one line, that you are watching and will answer in the note.
2. When it exits:
   - **0, new marks:** `list` the note, then answer each of the human's marks in the document. A comment
     asking for a change: a `suggest` with `--why`, then `resolve <comment> --addressed-by <suggestion>`.
     A question, or a disagreement: reply with `comment --as editor --on <mark>`. Their own suggestion with
     no comment attached: `accept` it. Never reject theirs. Then re-arm.
   - **1, timeout:** re-arm silently.
   - **2, conflict copy:** stop writing. Tell the human a sync conflict copy appeared and that they must
     reconcile it before you continue.
3. Keep going until the human says stop. Say nothing in chat for a quiet re-arm; the conversation happens in
   the note.
