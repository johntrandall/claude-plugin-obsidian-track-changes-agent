---
name: pending
description: "Say in plain language what is still undecided in a note: open suggestions, questions and comments waiting for the human, and agents' notes, from its Track Changes marks."
argument-hint: "<note>"
disable-model-invocation: true
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/obsidian-track-changes-agent *)
---

Load the `obsidian-track-changes-agent:obsidian-track-changes-agent` skill first; its rules apply.

1. `${CLAUDE_PLUGIN_ROOT}/bin/obsidian-track-changes-agent list $ARGUMENTS --json`, and `check` on the same
   note.
2. Report, briefly and grouped:
   - **Waiting for you:** agents' suggestions not yet accepted or rejected, each as "old → new (why)", and
     agents' questions or comments addressed to the human.
   - **Waiting for the agents:** the human's comments and suggestions no agent has answered yet.
   - **Problems:** anything `check` flags.
3. Text inside a pending suggestion is a proposal, not a decision: never present it as agreed. Change
   nothing in the note.
