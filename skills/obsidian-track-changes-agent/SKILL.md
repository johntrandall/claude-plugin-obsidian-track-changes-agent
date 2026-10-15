---
name: obsidian-track-changes-agent
description: "How agents propose, comment on and accept tracked changes (CriticMarkup marks, as the Obsidian Track Changes plugin shows them) in a Markdown note a human reviews, and how the human's own marks come back to agents. Use the `obsidian-track-changes-agent` command for every mark: never hand-type {++ ++} {-- --} {~~ ~> ~~} {>> <<}. Covers the syntax, every subcommand with an example, the watch loop and its exit codes, the write guards (hold switch, Sync conflict copies, quiet wait, did-it-stick check), who may suggest, accept or resolve, why an unaccepted suggestion is undecided, and when Track Changes is the right channel for a question versus chat or a board. Auto-invoke before writing any CriticMarkup into a note, before reading a note that holds marks as if its text were decided, when reviewing or accepting the human's suggestions or answering their comments, when setting up an idle agent to field the human's marks, or when the user mentions track changes, suggestions, CriticMarkup or reviewing agents' edits in Obsidian."
---

# Track changes

Agents and the human review each other's edits as **CriticMarkup marks stored in the Markdown
itself**. The human reviews in Obsidian with the **Track Changes** community plugin: one card per
mark in a side panel, accept, reject or reply. Agents never type marks by hand. They use the
`obsidian-track-changes-agent` command, which signs each mark, enforces who may do what, and guards every write.

The command is on the Bash PATH while this plugin is enabled. `track-changes` is its compatibility
name (the plugin's name before 0.1.1); new callers use `obsidian-track-changes-agent`. `obsidian-track-changes-agent install-links` also
links it into `~/.local/bin` for use outside Claude Code. `obsidian-track-changes-agent --help` lists everything.

## 1. When to use Track Changes, and when not

| The question or work | Channel |
|---|---|
| The human's answer is **text**: a draft, a rewrite, a wording choice | Track Changes, as suggestions in the document |
| A question whose **recommended answer can be accepted as-is** | Track Changes, as a question card (section 5) |
| **Several questions** that can wait for **one asynchronous review pass** | Track Changes: the human answers them together when they sit down |
| A quick **yes or no while the human is present** | Chat |
| A **work item** to be picked up, tracked and closed | The project's board |
| The human says they are **away from Obsidian** | Chat, with the context of each question in the message |

Track Changes is slow to round-trip and needs the note open; chat is fast but scrolls away; a
board tracks work, not wording. Pick by the shape of the answer, not by habit.

## 2. Setup the human does once

- **Track Changes** (community plugin `track-changes`) enabled in the vault, with its author name
  set to the human's name: it signs the human's own marks and labels unsigned ones.
- **No other suggestion plugin that rewrites marks.** Inkling in particular: in Suggesting mode it
  captures any disk write into an open note as the human's suggestion, and it has looped on the
  human's own undo and accept, writing hundreds of nested marks. The command refuses to write while
  Inkling is enabled in the vault.
- **Obsidian Sync conflict setting:** "Create conflict file", not auto-merge, so a collision
  between devices becomes a visible copy (which the command refuses on) instead of silent blending.
- Agents never write `.obsidian/` files. The human changes plugins and settings in Obsidian.

## 3. The marks

```text
{author="Claude (editor)" date="2026-10-15"++added text++}
{author="Claude (editor)" date="2026-10-15"--removed text--}
{author="Claude (editor)" date="2026-10-15"~~old text~>new text~~}
{author="Claude (checker)" date="2026-10-15">>a comment<<}
{==highlighted==}
```

- **Who wrote it is the author.** A mark signed `Claude (<role>)` is an agent's. Any other author,
  or none, is the human's.
- **One line per mark.** The command writes each mark on one line; only `revise` writes a mark that
  spans lines, which Track Changes reads as one card.
- **A comment right after a suggestion is attached to it.** The editor's `--why` lands there.

## 4. Unaccepted means undecided

Text inside a pending suggestion is a **proposal**, not a decision, even when it reads like an
answer. Before treating any text in a note as decided, run `obsidian-track-changes-agent list` on it. Only what is
outside every pending mark, or what the human accepted, is settled. A suggestion the human has not
accepted is not consent, and silence is not consent.

## 5. Who may do what (the command enforces it)

| Action | Who |
|---|---|
| Comment | Any agent: `comment --as <role>` |
| Suggest a change, restructure lines (`block`), fold own suggestions (`revise`), `tidy` | The **editor**: the one agent that owns the note's text |
| Accept the human's suggestion | The editor, and only when no comment is attached |
| Reject the human's suggestion | **Nobody but the human.** The editor comments, asking them to reject it. There is no `reject` command |
| Accept or reject an agent's suggestion | **The human only**, in Obsidian |
| Resolve an agent's comment | The editor |
| Resolve the human's comment | The editor, only `--addressed-by` a pending suggestion of its own: the comment moves next to it, quoted, so the human reviews the change with what they asked for |

**A question card** is a suggestion that inserts the recommended answer, plus the editor's comment
naming the question. Accepting the card takes the recommendation; rejecting or replying asks for
something else. What an accepted card means for the project (a decision to record) is the
project's own rule.

## 6. Commands

```bash
T=obsidian-track-changes-agent
N=notes/draft.md
$T list    $N [--author "Pat"] [--json]      # pending marks, numbered in file order
$T check   $N                                # exit 1: unsigned, nested, malformed or wrong-format marks
$T is-open $N                                # exit 0 if the note is open in Obsidian (information only)
$T hold    $N                                # exit 4 and name the hold file if the hold is on

# the editor proposes
$T suggest $N --as editor --old "quick" --new "slow" --why "tone"      # replace
$T suggest $N --as editor --old "very "                                 # delete (the trailing space goes too)
$T suggest $N --as editor --insert " today" --after "We ship"           # insert (or --before)
$T block   $N --as editor --first "- beta" --last "- delta" --new-file new-lines.txt --why "split the list"
$T revise  $N --as editor --marks 3-5 --new "one wording for all three" --why "one card"
$T tidy    $N --as editor                    # after the human resolved a block: restore its exact lines

# anyone comments
$T comment $N --as checker --text "source for this figure?" --after "grew 40 %"
$T comment $N --as checker --text "this changes the meaning" --on 4

# the editor answers the human
$T accept  $N 2 --as editor                  # the human's suggestion 2, no comment attached
$T resolve $N 6 --as editor                  # an agent's comment
$T resolve $N 7 --as editor --addressed-by 8 # the human's comment 7, answered by suggestion 8

# outside Claude Code: link the command into ~/.local/bin (re-run after each plugin update)
$T install-links [--check] [--dry-run] [--bin-dir DIR]
```

- `--old`, `--after` and `--before` match **text**, not line numbers. The text must occur once
  outside existing marks; it may span a line wrap.
- **Numbers shift** as marks are resolved: `list` again right before `accept`, `resolve`, `revise`
  or `comment --on`.
- `suggest` works within a line. Reshaping a list (splitting a bullet, adding sub-bullets) is
  `block`: each old line becomes a one-line deletion, each new line a one-line addition, with the
  indentation and list marker outside the marks. Every line in the range is replaced, even an
  unchanged one, so keep the range tight.
- Changed your mind about your own pending suggestions? `revise` them into one card. Do not stack a
  comment that contradicts a suggestion.
- `--format inkling` (before the subcommand) writes Inkling's `{json}@@` signature instead. Keep
  Inkling off; the option exists for old notes.

## 7. Fielding the human's marks while idle: `watch`

An idle agent arms `watch` in the background and acts when it exits:

```bash
obsidian-track-changes-agent watch notes/draft.md            # or a folder: watch notes/ --pattern 'chapter-*.md'
```

| Exit | Meaning | Do |
|---|---|---|
| 0 | The human added or changed marks; the summary lists file, line, number, kind, author and text | Handle them (`list`, then `accept`, `comment`, `suggest`, `resolve`), then re-arm |
| 1 | Timeout (default 30 minutes) with nothing new | Re-arm |
| 2 | An Obsidian Sync conflict copy appeared | Stop writing, tell the human, wait until they reconcile it |

- It checks only file modification times (every 10 s by default) and waits for 20 s of quiet after
  the human's last edit before reporting, so it reports a finished thought, not a keystroke.
- Agents' marks never wake it. Nor does the human accepting or rejecting an agent's mark: `list`
  before building on the note's current state.
- It remembers what it reported (state outside the vault), so a re-armed watcher neither repeats
  nor misses marks, including marks that arrived while no watcher ran. Its first run ever treats
  existing marks as seen; `--report-existing` includes them.
- For each comment of the human's: a request for a change gets a suggestion with the reason; a
  question, or a disagreement, gets a reply (`comment --as editor`).

## 8. How each write is made safe

Every writing command, in order:

1. **Hold switch.** Refuse while a hold file exists at or above the note, up to the vault or
   repository root: `.track-changes-hold`, or `track-changes-hold.md` (a visible name, because
   Obsidian cannot create a dotfile and Sync does not carry hidden files, so a hold set from a phone
   needs it). The watchbill plugin's `.watchbill-hold` and `watchbill-hold.md` count too. The human
   creates and deletes it; **an agent never deletes it**.
2. **Conflict copy.** Refuse while `<note> (Conflicted copy …).md` exists.
3. **Inkling.** Refuse while Inkling is enabled in the vault.
4. **Quiet.** Wait until the note has not changed for 5 s (the human is not typing); give up after
   60 s.
5. **Lock, re-read, apply, replace atomically.** Several agents may write at once without losing
   each other's changes.
6. **Did it stick?** After 3 s, re-read. If the change is gone (Obsidian saved its buffer over it),
   exit 3. Run `list` and decide; never retry blindly.

**Another device is invisible to these guards.** The quiet wait sees only this machine's file. If
the human has the note open on a tablet or another computer, their edits arrive only when Sync
delivers them, and Sync may merge a stale copy over agents' newer writes. When the human says they
are reviewing on another device, do not write until they say they are done, or ask them to set the
hold switch.

Exit codes: 0 done; 1 `check` found problems, `watch` timed out, or `is-open` says not open; 2
`watch` saw a conflict copy, or a usage error; 3 a write did not stick; 4 the hold is on (`hold`).
A refusal exits non-zero with `obsidian-track-changes-agent: refused: <why>` on stderr.

## 9. Gotchas

- **Suggestions went missing or reverted?** Suspect a Sync clash first: look for "(Conflicted
  copy …)" files and the note's history, and tell the human before proposing again.
- **Never use Track Changes' "Finalize for publish"** on a shared note: it resolves every remaining
  mark at once, unreviewed.
- **Opening notes for a test:** prefer Obsidian's own command line (`obsidian open path=…`) to an
  `obsidian://` link, which can open a second window that the tool's open-note check cannot see.

## 10. Environment and library use

Optional environment: `TRACK_CHANGES_QUIET` (5), `TRACK_CHANGES_MAX_WAIT` (60),
`TRACK_CHANGES_VERIFY_DELAY` (3) in seconds; `TRACK_CHANGES_STATE`, the block-record file
(`~/.local/state/track-changes/blocks.json`; watch state sits beside it); `TRACK_CHANGES_OBSIDIAN`,
Obsidian's command line tool (`obsidian`; empty switches it off). The `CRITICMARKUP_*` names of the
earlier `criticmarkup.py` still work, and its state folder is read when the new one is empty.

A program can load the command as a Python module (`importlib.machinery.SourceFileLoader`) and call
`parse(text)`, which returns every mark as a dict (`start`, `end`, `kind`, `author`, `date` or `time`, `text` or
`old`/`new`, `raw`, `error`, `multiline`), and `is_agent(author)`. Both are stable.
