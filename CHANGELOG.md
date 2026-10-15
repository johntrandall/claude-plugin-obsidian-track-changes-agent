# Changelog

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
plugin (watchbill 0.4.0, its last change there 2026-10-14).

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
