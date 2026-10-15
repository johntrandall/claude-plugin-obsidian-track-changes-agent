# obsidian-track-changes-agent

A Claude Code plugin that lets AI agents propose edits and comments in your Obsidian notes as tracked
changes. You accept, reject or reply with the Obsidian Track Changes plugin, and an agent watching the note
answers you as you go.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## In plain terms

When an AI agent helps you write, it is hard to see what it changed and to keep the final say. This plugin
makes the agent propose its changes the way a colleague would in a word processor: as a suggestion you
accept or reject, with a note saying why. You answer in Obsidian, and the agent answers back.

- **It feels like working with a colleague:** leave a comment or an edit in the note, and about half a
  minute after you stop typing, the agent watching it replies, makes the change you asked for, or asks you
  a question, right there in the document. No chat window, no copy and paste.
- **You stay in charge:** through this plugin, an agent cannot accept its own suggestion or reject one of
  yours. You decide in Obsidian.
- **Your typing is protected:** on the computer where the agents run, an agent waits until you pause and
  checks afterwards that its change stuck. If you edit on another device, use the hold switch.
- **One switch stops every write:** create a note called `track-changes-hold`, even from your phone, and
  every write through the command stops until you delete it.
- **Questions wait for you:** several questions can sit in the document until one review pass, instead of
  interrupting you in chat.
- **No Git needed:** you review the way you would in a word processor, not as diffs, branches and pull
  requests.

## When to use it

It is best after you have approved a version of a document. From then on, every change an agent proposes
through this plugin arrives as a suggestion (it applies directly only your own comment-free suggestions, tidies
blank lines and removes comments), so you see exactly what changed since your approval and decide each one. Early in
drafting, while the text is still taking shape, it is less friction to let the agent write directly and
keep going; switch to suggestions once you have signed off a draft.

It is not for code or for changes that span many files (use Git); not for assistants that cannot run shell
commands; not yet for Windows; and the reviewing side needs Obsidian with the Track Changes plugin.

## What it does

The plugin includes one command-line utility, `obsidian-track-changes-agent`, designed for agentic use, a
skill that teaches Claude when and how to use it, and three slash commands for the common requests.
Together they extend the review workflow that the Obsidian Track Changes plugin enables, so agents can take
part in it with guard rails. The agent proposes text, comments and answers your replies; you decide in
Obsidian; and an agent in watching mode (`watch`, below) answers you as you work.

### CriticMarkup and Track Changes

The marks are CriticMarkup, an open, plain-text syntax for editorial marks in any text file. Its
specification is the [syntax section](https://github.com/CriticMarkup/CriticMarkup-toolkit#the-basic-syntax)
of the CriticMarkup toolkit's README on GitHub; the original site, criticmarkup.com, is no longer online.
It has five marks: `{++added++}`, `{--removed--}`, `{~~old~>new~~}`, `{>>comment<<}` and `{==highlight==}`.

[Track Changes](https://obsidian.md/plugins?id=track-changes), an Obsidian community plugin by Phil Baum,
shows those marks as review cards you accept, reject or reply to. It adds per-mark metadata
(`author="…" date="…"`) so each card says who made it. This command writes that signed form and signs
every agent's mark `Claude (<role>)`. The agent declares its role in brackets, and the command allows only
that role's actions: the `editor` proposes text, and any other role, such as `checker`, only comments.

```text
We ship the beta {author="Claude (editor)" date="2026-10-15"~~on Friday~>next Tuesday~~}{author="Claude (editor)" date="2026-10-15">>QA needs two more days<<}.
```

The marks stay plain text in the note, so any CriticMarkup-aware tool can read them.

### Watch: the collaboration loop

`watch` is what makes this feel like collaboration rather than a batch job. An agent arms it on a note, or
on a folder of notes, and waits. Nothing happens until you write:

1. You reply to a card, leave a comment ("too formal"), or make an edit of your own as a suggestion.
2. About 20 seconds after you stop typing, `watch` wakes the agent with a summary of your new marks.
3. The agent answers in the document, usually within half a minute of your last keystroke: it replies to
   your comment, proposes the change you asked for as a new suggestion, or accepts your edit. Then it goes
   back to watching.

It also notices your decisions. When you accept or reject one of its cards, `watch` reports which, and the
agent is told to tidy up after a whole-line change and not to propose a change you rejected again.

Waiting costs almost nothing: `watch` only checks the files' modification times every 10 seconds, and the
agent does no work until something arrives. It remembers what it has already reported, so it does not repeat
itself, and it picks up marks you made while it was busy. (The first watch on a note or folder counts the marks
already there as seen; a note added to a watched folder later is watched in full.) If your sync service keeps two versions of the note and adds a second file (a
conflict copy), `watch` stops and reports it, and agents do not write until you reconcile the two.

## Why it exists

The problems it solves when agents edit a note you are reviewing:

- **Track Changes alone does not guard agents' writes.** It shows review cards for anyone's marks, but
  nothing in it makes an agent sign its marks, wait for your typing, respect a hold, or answer your
  replies. This plugin adds that agent side.
- **Malformed marks.** Agents typing CriticMarkup by hand sometimes get it wrong: unsigned marks (Track
  Changes shows them under your name, so they look like yours) and nested marks (the inner mark gets no
  card). The command writes every mark the same, checked way.
- **Writes that collide with your typing.** An agent saving while you type can lose your keystrokes or its
  own change. The command waits for a pause, takes a lock so two agents cannot overwrite each other, and
  checks afterwards that its change stuck.
- **Agents that overstep.** Without rules, any agent can rewrite the text or accept its own suggestions.
  The command accepts text proposals only from the `editor` role (an agent declares its role itself) and
  lets other roles only comment, and the skill names the `editor` as the one agent that owns a note's
  text.
- **Clashes between devices.** When your sync service has kept two versions of a note, the command stops
  writing until you sort them out.
- **No way to say stop.** The [hold switch](#the-hold-switch) stops every write through the command at once.
- **Replies that go unanswered.** `watch` answers your marks while you work.

## Why not just use Git?

Git is the usual way to review an agent's work: the agent edits files, and you read a diff or a pull request.
That suits code. For a document that people and agents write together, it is often too heavy. This plugin is
an alternative to Git-based review workflows for that case.

- **Review happens in the document.** Each change is a card beside the sentence it changes. You go through
  them word-processor style, at reading speed, with no diff viewer, branch or commit in the way.
- **Several agents can work on one long document at once.** An editor's suggestions and other agents'
  comments are small marks anchored to their own text in the same file. They do not sit on competing
  branches that someone has to merge.
- **Code work and document review stay out of each other's way.** In a repository where agents are changing
  code, reviewing the documentation needs no branch, worktree or merge of its own: the review lives in the
  marks inside the documents, so code commits and your review decisions never wait on each other.
- **You decide change by change.** Accept three suggestions, reject one, reply to another. A pull request
  asks you to take or return a whole batch.
- **The reviewer needs no Git.** Anyone who can use Obsidian can review, including people who never touch a
  terminal.
- **You can commit work you have not reviewed yet.** A pending suggestion is finished work waiting for your
  decision, and it is plain text. Commit the note with its marks still in it: agents keep moving forward on
  top, and your accept or reject later is just another commit. There is no holding branch for unreviewed
  work and nothing to rebase.

Use Git instead for code, for changes that span many files, and for rewrites you review as a whole.

## Why not an MCP server?

The work is editing files in the folder the agent is already working in, so a command does it with fewer
moving parts:

- **Nothing to run or configure.** The command is a single script on the PATH. There is no server process,
  port or connection to set up, and nothing keeps running between sessions.
- **Any caller can use it.** Agents, scripts, Git hooks and scheduled jobs all run it the same way; you can
  too, from a terminal. An MCP server would serve MCP clients only.
- **Waiting fits a command.** `watch` waits, sometimes for many minutes, until you mark something. An agent
  runs it as a background job and picks up the result, which suits a command better than a long-blocking
  MCP tool call.
- **The safety is in the command.** The lock, the pause for your typing and the check that a change stuck
  apply to every caller, so a server would add a process without adding protection.

The cost: assistants that cannot run shell commands, such as a chat app without a terminal, cannot use it.

**Tied to Claude Code, for now.** The packaging, the `Claude (<role>)` signature and the slash commands are
Claude Code specific. The command itself is a plain Python script that any agent able to run shell commands
can call. An agent-neutral signature and packaging are under review: see [ROADMAP.md](ROADMAP.md).

## Install

### Requirements

| For | You need |
|---|---|
| Agents (this plugin) | macOS or Linux (the write lock uses a Unix-only call; Windows is on the roadmap), Claude Code, and Python 3 (preinstalled on most Linux systems; on macOS it comes with the Xcode Command Line Tools). Claude Code plugins cannot declare a dependency on Python, so the plugin checks when a session starts and tells you if Python 3 is missing |
| You (reviewing) | Obsidian with the [Track Changes](https://obsidian.md/plugins?id=track-changes) community plugin enabled in the vault, its "Your name" setting set to your own name. Without it you see raw `{~~old~>new~~}` marks instead of review cards |
| Optional | A sync service such as Obsidian Sync, to review on another device. With Obsidian Sync, set conflict handling to "Create conflict file" on every device, so a clash between devices leaves a visible conflict copy (a second file named `<note> (Conflicted copy …).md`); the command then stops writing |

Keep the Inkling plugin (another Obsidian suggestion plugin) switched off in the same vault: it rewrites marks, and the command refuses to write
while it is enabled.

### Install the plugin

In Claude Code:

```text
/plugin marketplace add johntrandall/claude-plugin-obsidian-track-changes-agent
/plugin install obsidian-track-changes-agent@obsidian-track-changes-agent
```

That is all agents need: inside Claude Code the command is on the PATH of every session.

### Optional: the command outside Claude Code

To run the command yourself, from your own terminal, a script or a scheduled job (for example to list the
marks still pending in a note), link it into `~/.local/bin`. Agents in Claude Code do not need this.

```bash
obsidian-track-changes-agent install-links   # run it again after each plugin update
```

## Quick start

1. Open Claude Code in the folder that holds your note (your vault, or a repository of Markdown files).
2. Ask for edits as suggestions:

   ```text
   Tighten the wording of notes/launch-plan.md. Propose each change as a tracked suggestion
   with a short reason, and don't edit the text directly.
   ```

3. Open the note in Obsidian, then the review panel (command palette: "Track Changes: Open review panel").
   Accept, reject or reply to each card.
4. Keep the conversation going. This is the part that makes it feel like working together:

   ```text
   Watch notes/launch-plan.md for my replies and answer them.
   ```

   Now reply to a card or leave a comment in Obsidian. About half a minute after you stop typing, the
   agent's answer appears in the note.

Or use the slash commands, which say the same thing the same way every time:

| Slash command | What the agent does |
|---|---|
| `/obsidian-track-changes-agent:suggest <note> [what to change]` | proposes its edits as suggestions, each with a reason |
| `/obsidian-track-changes-agent:watch <note or folder>` | watches and answers your marks as you make them, until you say stop |
| `/obsidian-track-changes-agent:pending <note>` | says in plain words what is still undecided, and by whom |

With several agents on one document, name one editor and let the others comment:

```text
You are the editor of notes/launch-plan.md. Start two checkers, one for facts and one for style.
They only comment; you turn their points into suggestions.
```

## The hold switch

The hold switch stops every write made through the command. When to use it:

- **You are reviewing on another device.** The command cannot see your typing on a phone or tablet, and a
  sync merge could lay your older copy over the agents' newer writes (see Known limit, under Status).
- **You are rewriting the note yourself** and do not want suggestions landing in the middle of it.
- **An agent is misbehaving.** One file stops every write through the command at once, without finding
  each session.
- **The document is final.** Freeze it before you send or publish it.

How it works:

- **Turn it on:** create a note named `track-changes-hold` at the top level of your vault. On a phone, use
  Obsidian's "New note" in the vault's root folder. Your sync service carries the file
  (`track-changes-hold.md`) to the computer where the agents run.
- **While it is on:** every write through the command stops with "the human's hold switch is on". The
  skill tells agents never to delete the file. Reading still works, and a write that has already started
  finishes.
- **Turn it off:** delete the note. (The hold files of the watchbill plugin, `.watchbill-hold` and
  `watchbill-hold.md`, count too.)
- **Hold one folder only:** put the note in that folder instead. The command looks for it in the note's
  own folder and every folder above it, up to the vault's top level (in a plain Git repository, the
  repository root).
- **From a terminal:** an empty file named `.track-changes-hold` works too. The visible `.md` name exists
  because Obsidian hides files whose names start with a dot, and Obsidian Sync does not carry them.
- **Check it:** `obsidian-track-changes-agent hold <note>` says whether a hold applies to that note.

The hold takes effect when the file reaches the agents' computer, so allow for your sync service's delay.

## How it works

| Command | Who | Does |
|---|---|---|
| `list`, `check`, `is-open`, `hold` | anyone | read: pending marks, malformed marks, whether Obsidian has the note open, whether the hold is on |
| `comment` | any agent | adds a signed comment after a phrase or on mark N |
| `suggest` | the editor | proposes a replacement, deletion or insertion, with a reason |
| `block`, `tidy` | the editor | replaces whole lines (reshaping a list) as one-line marks; afterwards removes the empty lines Track Changes leaves |
| `revise` | the editor | folds several of its own pending suggestions into one card |
| `accept` | the editor | accepts one of your suggestions that has no comment attached |
| `resolve` | the editor | removes an agent's comment, or yours once a pending suggestion addresses it |
| `watch` | any agent | waits for your new marks and your accepts and rejects |

### Who decides

- **Agents' suggestions: only you.** The command refuses to let any agent accept or reject a suggestion
  made by an agent, its own included, and it has no override, not even if you tell the agent to in chat.
  You accept or reject in Obsidian. An agent that edited the file by hand instead could still do it; see
  Deleting markup.
- **Your suggestions: you, or the editor when there is nothing to discuss.** The editor may accept one of
  your suggestions that has no comment attached. It never rejects yours: if it disagrees, it comments with
  its reasons, and you reject it yourself if you agree.
- **Comments.** The editor removes agents' comments when they are done. It removes yours only once one of
  its suggestions addresses them, and then your comment moves next to that suggestion, quoted, so you
  review the change together with what you asked for.
- **Its own pending cards.** The editor may fold several of them into one new card. Nothing is accepted;
  the original text stays as the new card's "before".
- **Deleting markup.** No command removes marks wholesale. An agent that edited the file directly, instead
  of through the command, could; the skill forbids it, but nothing blocks it yet (see Roadmap). To clear
  all markup yourself, Track Changes' "Finalize for publish" resolves every remaining mark at once. Do not
  use it on a note others are still reviewing.

### Every write is guarded

Every write refuses while the hold switch is on, while a sync conflict copy of the note exists, or while
the Inkling plugin is enabled. It then waits for 5 seconds without edits, locks the note, re-reads it,
replaces it atomically, and after 3 seconds checks the change is still there, and says so if it is not.

The skill (`skills/obsidian-track-changes-agent/SKILL.md`) covers the rest: an example for every command,
the exit codes, the watch loop, why an unaccepted suggestion is not a decision, and when Track Changes is
the right channel for a question rather than chat or a task board.

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

Beta. Tested with Track Changes 2.2.0 and Obsidian Sync. The command began as `criticmarkup.py` inside the
[watchbill](https://github.com/johntrandall/claude-plugin-watchbill) plugin, which still bundles it in its
current public release; the next watchbill release uses this plugin instead.

- **Known limit: editing on another device.** The command's check for your typing sees only the computer
  where the agents run. If you edit the note on your phone or another computer, your edits arrive only when
  your sync service (Obsidian Sync, iCloud or similar) delivers them, and the service may merge your older
  copy over the agents' newer writes. Use the hold switch while you review on another device.

## Roadmap

What comes next, and what is under review: [ROADMAP.md](ROADMAP.md). Ideas and votes are welcome as
GitHub issues.

## Contributing

Open an issue with the note's marks (before and after) and the command you ran. Pull requests are welcome;
run `python3 tests/test_obsidian_track_changes_agent.py` first.

## License

[MIT](LICENSE)
