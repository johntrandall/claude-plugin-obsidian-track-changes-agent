# Changelog

## 0.1.9 (2026-10-15)

- Fix: `watch` keyed its memory on the files it found, so a note added to a watched folder started a new
  baseline and its unreported marks were silently treated as seen. Memory is now keyed on what you asked it
  to watch; a watch armed by an earlier version keeps its memory.
- README, round 3 of the cold verifiers: what "through this plugin" covers (the editor applies only your
  comment-free suggestions and tidies blank lines directly); the hold switch stops writes through the
  command, not every agent; the lock is against agents overwriting each other. Round 4: the same for the
  plain-terms bullet; comment removal named; `watch` reports a conflict and agents hold off; Inkling named
  as an Obsidian plugin; watchbill's hold files mentioned.

## 0.1.8 (2026-10-15)

- Fix: `watch` on a folder skipped every note whose file name contains a space (most Obsidian notes). It
  now skips only sync conflict copies.
- README, after two cold verifiers (facts and links; reader experience): the hook no longer leans on
  "CriticMarkup" before defining it; "When to use it" moved up, with who it is not for; claims calibrated
  to what the command enforces (the `editor` is a role; hand edits could bypass it); "Track Changes alone
  is for people"; "Tied to Claude Code, for now"; one timing story for `watch` (wakes about 20 seconds
  after you stop typing, answer within about half a minute); conflict copies named; Obsidian Sync's
  conflict setting is per device; the hold search stops at a Git repository's root too; the watchbill
  history corrected (its current public release still bundles the old script); exit codes left to the
  skill; Track Changes' handling of unsigned and multi-line marks stated correctly (round 2).

## 0.1.7 (2026-10-15)

- README: the CriticMarkup links pointed at criticmarkup.com, which is no longer online (a parked page; the
  front page redirects to the toolkit on GitHub). The README now links the syntax section of the toolkit's
  README, which is the specification.
- ROADMAP: ignore CriticMarkup examples inside code.
- When to use it (README and skill): best after you have approved a version, to see every later change;
  early in drafting, let the agent write directly.

## 0.1.6 (2026-10-15)

- `watch` also wakes when you accept or reject one of an agent's suggestions, and says which (judged from
  the text left behind). The editor's own `revise` is not reported. Watch state now records agents'
  suggestions too; the earlier state format is still read.
- README: "Who decides" (agents' suggestions are yours alone, no override; what the editor may do with
  yours and with comments; deleting markup), macOS or Linux in the requirements, `watch` noticing your
  decisions, and a link to the new ROADMAP.md.

## 0.1.5 (2026-10-15)

- Three slash commands: `/obsidian-track-changes-agent:suggest`, `:watch` and `:pending`. Only you can
  start them; they run the bundled command without permission prompts.
- README: the slash commands in the quick start, and when to use the hold switch.

## 0.1.4 (2026-10-15)

- README: "Why not an MCP server?"; the command is described as designed for agentic use.
- README: `watch` featured as the collaboration loop (hook, plain terms, its own section, quick start);
  "Why not just use Git?".

## 0.1.3 (2026-10-15)

- The `track-changes` command alias is gone: next to the Obsidian plugin of that name it was confusing.
  Use `obsidian-track-changes-agent`. An old `~/.local/bin/track-changes` link is left alone; remove it
  yourself.
- A session-start check says so when Python 3 is missing (Claude Code plugins cannot declare a dependency
  on it). It never runs `python3` itself, so it cannot open macOS's install dialog.
- README reworked: the CriticMarkup standard and how Track Changes extends it; why the plugin exists as a
  list of the problems it solves; the hold switch, including from a phone; Git (code and document review
  stay out of each other's way; unreviewed suggestions can be committed); what `install-links` is for; a
  quick start that shows what to ask an agent; the multi-device limit spelled out.

## 0.1.2 (2026-10-15)

- README: "Why not Git?", the case for in-document review over diffs and pull requests when people and
  agents write a document together (including a parallel review channel for documentation in a repository
  where agents change code at the same time, without worktrees), and a plain-terms line saying no Git is
  needed.

## 0.1.1 (2026-10-15)

The first public release.

- Renamed to `obsidian-track-changes-agent` (plugin, command, skill, repository), because the Obsidian
  Track Changes plugin's own id is `track-changes`. `track-changes` stays as the command's compatibility
  name, and `install-links` links both. Environment names (`TRACK_CHANGES_*`), the state folder
  (`~/.local/state/track-changes/`) and the hold file names are unchanged.
- README: a Requirements section that says what the human side needs (Obsidian and its Track Changes
  plugin) and that this plugin is its companion, not part of it.
- The skill's command block shows `install-links` (cold verifier, 2026-10-15).
- README: the Status section says which watchbill releases bundled the tool.

## 0.1.0 (2026-10-15)

First release as its own plugin. The command was `criticmarkup.py`, bundled with the watchbill
plugin (last changed there on 2026-10-14; watchbill's public release 0.3.2 still bundles it).

- Renamed to `track-changes`; the plugin is `track-changes`, the skill `track-changes`.
- Self-contained: the hold switch is built in. It honours `.track-changes-hold` and
  `track-changes-hold.md`, and still the watchbill names `.watchbill-hold` and `watchbill-hold.md`.
- New `hold <file>`: exit 4 and name the hold file while the hold is on.
- New `install-links`: links the command into `~/.local/bin` from the installed plugin (or a
  working tree with `--dev`).
- New `--version`.
- `list` shows the date of Track Changes-format marks; `parse()` returns it as `date`.
- `TRACK_CHANGES_OBSIDIAN` names Obsidian's command line tool, or switches it off when empty.
- State moved to `~/.local/state/track-changes/`; the old `~/.local/state/criticmarkup/` is read
  when the new folder has no copy, so block records and watch baselines carry over.
- Environment names are `TRACK_CHANGES_*`; the `CRITICMARKUP_*` names still work.
- Refusals say `track-changes: refused:`. The write lock keeps its old file name, so this command
  and an older `criticmarkup.py` lock each other out of the same note.
