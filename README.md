# obsidian-track-changes-agent

A Claude Code plugin for the agent side of Obsidian's Track Changes plugin: agents and a human review each
other's edits to a Markdown note as tracked changes.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## In plain terms

When an AI agent helps you write, it is hard to see what it changed and to keep the final say. This plugin
makes the agent propose every change the way a colleague would in a word processor: as a suggestion you
accept or reject, with a note saying why. You answer in Obsidian, at your own pace, and the agent picks your
answers up.

- **You stay in charge:** an agent can never accept its own suggestion or reject one of yours.
- **Nothing is lost while you type:** the agent waits until you pause, and checks afterwards that its change
  stuck.
- **One switch stops every agent:** a file named `track-changes-hold.md` in the vault, which you can create
  from your phone.
- **Questions wait for you:** several questions can sit in the document until one review pass, instead of
  interrupting you in chat.
- **No Git needed:** you review the way you would in a word processor, not as diffs, branches and pull
  requests.

## What it does

The plugin ships one command, `obsidian-track-changes-agent`, and one skill that teaches Claude to use it.
It is a companion to the Obsidian [Track Changes](https://obsidian.md/plugins?id=track-changes) community
plugin by Phil Baum, not part of it and not a replacement: the human reviews in that plugin, and agents write
through this command. The command reads and writes CriticMarkup marks (`{++added++}`, `{--removed--}`, `{~~old~>new~~}`, `{>>comment<<}`) in the
signed form Track Changes shows as review cards. It signs every agent mark as `Claude (<role>)`, lets only one agent (the editor) propose text,
and lets any agent comment. A `watch` mode waits cheaply for the human's new marks and exits with a summary,
so an idle agent can field review comments.

## Why it exists

Agents that type CriticMarkup by hand get it wrong: unsigned marks, marks wrapped across lines, nested marks,
and disk writes that land in the middle of the human's typing. Suggestion plugins can make it worse: one
captured an agent's disk write as the human's own suggestion and looped. This command makes the right thing
the only thing: it checks for the human's typing, a hold switch, a Sync conflict copy and a misbehaving
plugin before every write, takes a lock, and verifies the result.

## Why not Git?

Git is the usual way to review an agent's work: the agent edits files, and you read a diff or a pull request.
That suits code. For a document that people and agents write together, it is often too heavy. This plugin is
an alternative to Git-based review workflows for that case.

- **Review happens in the document.** Each change is a card beside the sentence it changes. You go through
  them word-processor style, at reading speed, with no diff viewer, branch or commit in the way.
- **Several agents can work on one long document at once.** An editor's suggestions and other agents'
  comments are small marks anchored to their own text in the same file. They do not sit on competing
  branches that someone has to merge.
- **It runs beside your Git work, not inside it.** When your documents already live as Markdown in a Git
  repository, agents can change code there while you and other agents review the documentation through
  Track Changes. That is a second, parallel review channel in the same checkout: no extra worktree, branch
  or merge for the prose.
- **You decide change by change.** Accept three suggestions, reject one, reply to another. A pull request
  asks you to take or return a whole batch.
- **The reviewer needs no Git.** Anyone who can use Obsidian can review, including people who never touch a
  terminal.
- **Git still fits underneath.** The note stays plain Markdown with plain-text marks, so you can keep
  versioning it with Git. Commit your own edits before agents write on top of them.

Use Git instead for code, for changes that span many files, and for rewrites you review as a whole.

## Install

### Requirements

| For | You need |
|---|---|
| The agent side (this plugin) | Claude Code and Python 3. Nothing else: the marks are plain text in any Markdown file |
| The human side (reviewing) | Obsidian with the [Track Changes](https://obsidian.md/plugins?id=track-changes) community plugin enabled in the vault, its author name set to your own. Without it you see raw `{~~old~>new~~}` marks instead of review cards |
| Optional | Obsidian Sync works; set its conflict handling to "Create conflict file" so a clash between devices is visible (the command then refuses to write) |

Keep the Inkling plugin switched off in the same vault: it rewrites marks and the command refuses to write
while it is enabled.

### Install the plugin

In Claude Code:

```text
/plugin marketplace add johntrandall/claude-plugin-obsidian-track-changes-agent
/plugin install obsidian-track-changes-agent@obsidian-track-changes-agent
```

The command is then on the Bash PATH of every Claude Code session. To use it in your own terminal too:

```bash
obsidian-track-changes-agent install-links   # links ~/.local/bin/; re-run after each plugin update
```

`track-changes` is the command's compatibility name (the plugin's name before 0.1.1); it does the same thing.

## Quick start

```bash
printf '# Launch note\n\nWe ship the beta on Friday.\n' > draft.md
obsidian-track-changes-agent suggest draft.md --as editor --old "on Friday" --new "next Tuesday" --why "QA needs two more days"
obsidian-track-changes-agent comment draft.md --as checker --text "Does marketing know?" --after "beta"
obsidian-track-changes-agent list draft.md
```

```text
suggestion written
comment written
#1   L3    comment      Claude (checker)       2026-10-15       'Does marketing know?'
#2   L3    substitution Claude (editor)        2026-10-15       'on Friday' -> 'next Tuesday'
#3   L3    comment      Claude (editor)        2026-10-15       'QA needs two more days'
```

Open `draft.md` in Obsidian and the Track Changes panel shows a card for each mark. An agent that is not the
editor cannot propose text:

```text
$ obsidian-track-changes-agent suggest draft.md --as checker --old "beta" --new "release"
obsidian-track-changes-agent: refused: only the editor may suggest text changes (you are 'checker')
```

## How it works

| Command | Who | Does |
|---|---|---|
| `list`, `check`, `is-open`, `hold` | anyone | read: pending marks, malformed marks, whether Obsidian has the note open, whether the hold is on |
| `comment` | any agent | adds a signed comment after a phrase or on mark N |
| `suggest` | the editor | proposes a replacement, deletion or insertion, with a reason |
| `block`, `tidy` | the editor | replaces whole lines (reshaping a list) as one-line marks; afterwards removes the empty lines Track Changes leaves |
| `revise` | the editor | folds several of its own pending suggestions into one card |
| `accept` | the editor | accepts one of the human's suggestions that has no comment attached |
| `resolve` | the editor | removes an agent's comment, or the human's comment once a pending suggestion addresses it |
| `watch` | any agent | waits for the human's new marks: exit 0 with a summary, 1 on timeout, 2 on a Sync conflict copy |

There is no `reject`: only the human rejects. Every write refuses while a hold file
(`.track-changes-hold` or `track-changes-hold.md`) sits at or above the note, while a Sync conflict copy
exists, or while the Inkling plugin is enabled. It then waits for 5 seconds without edits, locks the note,
re-reads it, replaces it atomically, and after 3 seconds checks the change is still there (exit 3 if not).

The skill (`skills/obsidian-track-changes-agent/SKILL.md`) covers the rest: the mark syntax, an example for every command,
the watch loop, why an unaccepted suggestion is not a decision, and when Track Changes is the right channel
for a question rather than chat or a task board.

## Configuration

No options are required. Environment variables, all optional:

| Variable | Default | Meaning |
|---|---|---|
| `TRACK_CHANGES_QUIET` | `5` | seconds without edits before a write |
| `TRACK_CHANGES_MAX_WAIT` | `60` | give up waiting for quiet after this many seconds |
| `TRACK_CHANGES_VERIFY_DELAY` | `3` | seconds before checking that a write stuck |
| `TRACK_CHANGES_STATE` | `~/.local/state/track-changes/blocks.json` | block records; watch state sits beside it |
| `TRACK_CHANGES_OBSIDIAN` | `obsidian` | Obsidian's command line tool; empty switches it off |

Programs can load the command as a Python module and call `parse(text)` and `is_agent(author)`.

## Status

Beta. The command has been in use since October 2026 as `criticmarkup.py`, bundled with the
[watchbill](https://github.com/johntrandall/claude-plugin-watchbill) plugin up to its 0.4 releases.
Later watchbill releases use this plugin instead. Tested with Track Changes 2.2.0 and Obsidian Sync.

- Known limit: the quiet wait sees only this machine's copy of the note; edits on another device arrive only
  when Sync delivers them.
- Next: a release on the public plugin catalog.

## Contributing

Open an issue with the note's marks (before and after) and the command you ran. Pull requests are welcome;
run `python3 tests/test_obsidian_track_changes_agent.py` first.

## License

[MIT](LICENSE)
