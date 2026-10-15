# Roadmap

**What this is:** what is planned for obsidian-track-changes-agent, roughly in order. Nothing here is
promised by a date. Ideas and votes are welcome as GitHub issues; see [CHANGELOG.md](CHANGELOG.md) for what
has shipped.

## Next

- **A guard against direct edits of marks.** Refuse an agent's file edit that would add, change or delete a
  CriticMarkup mark outside the command, so "only you decide" no longer rests on the skill's instructions
  alone. Edits through the agent's ordinary file tools can be caught reliably; shell edits only partly.
- **Windows support.** The write lock uses a Unix-only call today, so the command runs on macOS and Linux.
- **Automatic tidying.** Once you resolve every mark of a whole-line change, tidy the leftover blank lines
  without waiting to be asked.

- **Ignore marks inside code.** A CriticMarkup example written inside backticks or a code block is read as
  a live mark today; `list`, `check` and `watch` should skip it, and no command should change it.

## Under review

- **Agent-neutral identity and packaging.** Marks signed by any agent (`Codex (editor)`, `Gemini
  (checker)`, …) with a configurable list of agent names, and installs through the cross-agent
  [Agent Skills](https://agentskills.io) and Agent Plugins formats as well as the Claude Code plugin.
- **Safer review across devices.** Notice edits arriving by sync from another device instead of relying on
  the hold switch alone.

## Ongoing

- **Compatibility.** Check each new Track Changes release (mark format, metadata) and test with other
  CriticMarkup tools, such as other Obsidian CriticMarkup plugins.

## Done

- `watch` wakes when you accept or reject an agent's card, not only on your new marks (0.1.6).
