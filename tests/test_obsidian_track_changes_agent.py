#!/usr/bin/env python3
"""Tests for plugin/bin/obsidian-track-changes-agent: every subcommand, the write guards, watch, install-links,
the legacy (criticmarkup.py) state and environment names, and library use.

    python3 tests/test_obsidian_track_changes_agent.py        (or: python3 -m unittest discover tests)

No Obsidian, network or personal value is needed: each test builds a throwaway vault, points
the tool's state at it, and switches off Obsidian's command line tool (TRACK_CHANGES_OBSIDIAN="").
"""
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

sys.dont_write_bytecode = True
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The private repository keeps the plugin in plugin/; the public copy has it at the root.
TOOL = next(p for p in (os.path.join(ROOT, "plugin", "bin", "obsidian-track-changes-agent"), os.path.join(ROOT, "bin", "obsidian-track-changes-agent"))
            if os.path.isfile(p))


def load_module():
    """The tool loaded the way a caller loads it as a library (no .py suffix)."""
    loader = importlib.machinery.SourceFileLoader("track_changes_under_test", TOOL)
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("track_changes_under_test", loader))
    loader.exec_module(mod)
    return mod


tc = load_module()

EDITOR = 'author="Claude (editor)"'
HUMAN_SUB = '{author="Pat Example" date="2026-10-15"~~cat~>dog~~}'


class Vault(unittest.TestCase):
    """A temporary vault (with .obsidian) holding note.md, a private HOME and state folder."""

    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.home = os.path.join(self.d.name, "home")
        self.vault = os.path.join(self.home, "vault")
        os.makedirs(os.path.join(self.vault, ".obsidian"))
        self.note = os.path.join(self.vault, "note.md")
        self.state = os.path.join(self.d.name, "state", "blocks.json")
        self.env = {"TRACK_CHANGES_QUIET": "0", "TRACK_CHANGES_VERIFY_DELAY": "0", "TRACK_CHANGES_OBSIDIAN": "",
                    "TRACK_CHANGES_STATE": self.state, "HOME": self.home}

    def tearDown(self):
        self.d.cleanup()

    def write(self, text, path=None):
        with open(path or self.note, "w", encoding="utf-8") as f:
            f.write(text)

    def read(self, path=None):
        with open(path or self.note, encoding="utf-8") as f:
            return f.read()

    def run_tool(self, *args, env=None, drop=()):
        e = {k: v for k, v in os.environ.items() if not k.startswith(("TRACK_CHANGES_", "CRITICMARKUP_"))}
        e.update(self.env)
        e.update(env or {})
        for k in drop:
            e.pop(k, None)
        p = subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True, env=e, timeout=60)
        return p.returncode, p.stdout, p.stderr

    def ok(self, *args, **kw):
        code, out, err = self.run_tool(*args, **kw)
        self.assertEqual(code, 0, f"{args}: {out}{err}")
        return out

    def refused(self, *args, needle="refused", **kw):
        code, out, err = self.run_tool(*args, **kw)
        self.assertNotEqual(code, 0, f"{args} should be refused: {out}")
        self.assertIn(needle, err)
        return err

    def marks(self):
        return tc.parse(self.read())


# --- parsing and library use ------------------------------------------------------------------

class Parse(unittest.TestCase):
    def test_obsidian_track_changes_agent_signature(self):
        (m,) = tc.parse('a {author="Claude (editor)" date="2026-10-15"~~old~>new~~} b')
        self.assertEqual((m["kind"], m["author"], m["old"], m["new"], m["format"], m["date"]),
                         ("substitution", "Claude (editor)", "old", "new", "obsidian-track-changes-agent", "2026-10-15"))

    def test_every_kind(self):
        text = '{++a++} {--b--} {~~c~>d~~} {>>e<<} {==f==}'
        self.assertEqual([m["kind"] for m in tc.parse(text)],
                         ["addition", "deletion", "substitution", "comment", "highlight"])
        self.assertTrue(all(m["author"] is None for m in tc.parse(text)))

    def test_inkling_signature(self):
        (m,) = tc.parse('{++{"author":"Claude (editor)","time":1760000000}@@added++}')
        self.assertEqual((m["author"], m["time"], m["text"]), ("Claude (editor)", 1760000000, "added"))

    def test_problems(self):
        self.assertEqual(tc.parse("x {++never closed")[0]["error"], "unclosed")
        self.assertEqual(tc.parse("{~~no arrow~~}")[0]["error"], "substitution without ~>")
        self.assertTrue(tc.parse("{++a\nb++}")[0]["multiline"])

    def test_is_agent(self):
        self.assertTrue(tc.is_agent("Claude (editor)"))
        self.assertFalse(tc.is_agent("Pat Example"))
        self.assertFalse(tc.is_agent(None))

    def test_mark_round_trip(self):
        tc.FORMAT = "trackchanges"
        (m,) = tc.parse(tc.mark("~~", "editor", "x~>y"))
        self.assertEqual((m["author"], m["old"], m["new"]), ("Claude (editor)", "x", "y"))

    def test_env_prefers_new_name_then_legacy(self):
        saved = {k: os.environ.pop(k, None) for k in ("TRACK_CHANGES_QUIET", "CRITICMARKUP_QUIET")}
        try:
            self.assertEqual(tc.env("QUIET", 5), 5)
            os.environ["CRITICMARKUP_QUIET"] = "7"
            self.assertEqual(tc.env("QUIET", 5), "7")
            os.environ["TRACK_CHANGES_QUIET"] = "9"
            self.assertEqual(tc.env("QUIET", 5), "9")
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None)
                if v is not None:
                    os.environ[k] = v

    def test_version(self):
        p = subprocess.run([sys.executable, TOOL, "--version"], capture_output=True, text=True)
        self.assertEqual(p.stdout.strip(), f"obsidian-track-changes-agent {tc.VERSION}")


# --- reading: list, check, is-open --------------------------------------------------------------

class Read(Vault):
    def test_list_json_and_author_filter(self):
        self.write(f"The {HUMAN_SUB} sat.\n{{{EDITOR} date=\"2026-10-15\">>why?<<}}\n")
        rows = json.loads(self.ok("list", self.note, "--json"))
        self.assertEqual([(r["n"], r["kind"], r["author"]) for r in rows],
                         [(1, "substitution", "Pat Example"), (2, "comment", "Claude (editor)")])
        rows = json.loads(self.ok("list", self.note, "--json", "--author", "pat"))
        self.assertEqual(len(rows), 1)

    def test_list_empty(self):
        self.write("plain text\n")
        self.assertIn("no pending marks", self.ok("list", self.note))

    def test_check(self):
        self.write(f"ok {HUMAN_SUB}\n")
        self.assertIn("OK", self.ok("check", self.note))
        self.write("bad {++unsigned++}\n")
        code, out, _ = self.run_tool("check", self.note)
        self.assertEqual(code, 1)
        self.assertIn("unsigned", out)

    def test_check_flags_inkling_signature_in_track_changes_format(self):
        self.write('{++{"author":"Claude (editor)","time":1}@@x++}\n')
        code, out, _ = self.run_tool("check", self.note)
        self.assertEqual(code, 1)
        self.assertIn("Inkling signature", out)

    def test_is_open_reads_workspace_json(self):
        self.write("x\n")
        ws = os.path.join(self.vault, ".obsidian", "workspace.json")
        with open(ws, "w") as f:
            json.dump({"main": {"type": "leaf", "state": {"state": {"file": "note.md"}}}}, f)
        self.assertEqual(self.run_tool("is-open", self.note)[0], 0)
        with open(ws, "w") as f:
            json.dump({"main": {"type": "leaf", "state": {"state": {"file": "other.md"}}}}, f)
        self.assertEqual(self.run_tool("is-open", self.note)[0], 1)

    def test_missing_file(self):
        code, _, err = self.run_tool("list", os.path.join(self.vault, "nope.md"))
        self.assertNotEqual(code, 0)
        self.assertIn("no such file", err)


# --- writing: suggest, comment, accept, resolve ---------------------------------------------

class Suggest(Vault):
    def test_replace_delete_insert(self):
        self.write("The quick brown fox jumps.\n")
        self.ok("suggest", self.note, "--as", "editor", "--old", "quick", "--new", "slow", "--why", "tone")
        self.ok("suggest", self.note, "--as", "editor", "--old", "brown ")
        self.ok("suggest", self.note, "--as", "editor", "--insert", " high", "--after", "jumps")
        kinds = [(m["kind"], m["author"]) for m in self.marks()]
        self.assertEqual(kinds, [("substitution", "Claude (editor)"), ("comment", "Claude (editor)"),
                                 ("deletion", "Claude (editor)"), ("addition", "Claude (editor)")])
        self.assertEqual(self.marks()[2]["text"], "brown ")
        self.assertIn("Claude (editor)", self.read())
        self.assertIn("OK", self.ok("check", self.note))

    def test_insert_before(self):
        self.write("alpha omega\n")
        self.ok("suggest", self.note, "--as", "editor", "--insert", "beta ", "--before", "omega")
        self.assertEqual(tc.parse(self.read())[0]["text"], "beta ")
        self.assertTrue(self.read().startswith("alpha {author="))

    def test_phrase_across_a_line_wrap(self):
        self.write("one two\nthree four\n")
        self.ok("suggest", self.note, "--as", "editor", "--old", "two three", "--new", "2 3")
        self.assertEqual(self.marks()[0]["old"], "two three")

    def test_only_the_editor_suggests(self):
        self.write("text here\n")
        self.refused("suggest", self.note, "--as", "checker", "--old", "text", "--new", "t", needle="only the editor")

    def test_ambiguous_phrase(self):
        self.write("the cat and the cat\n")
        self.refused("suggest", self.note, "--as", "editor", "--old", "cat", "--new", "dog", needle="occurs 2 times")

    def test_text_inside_marks_is_not_matched(self):
        self.write(f"a {HUMAN_SUB} cat\n")
        self.ok("suggest", self.note, "--as", "editor", "--old", "cat", "--new", "bird")
        self.assertEqual(self.marks()[1]["old"], "cat")

    def test_inkling_format(self):
        self.write("hello world\n")
        self.ok("--format", "inkling", "suggest", self.note, "--as", "editor", "--old", "world", "--new", "there")
        self.assertIn('"author":"Claude (editor)"', self.read())


class Comment(Vault):
    def test_after_and_on(self):
        self.write(f"Some text. {HUMAN_SUB}\n")
        self.ok("comment", self.note, "--as", "checker", "--text", "source?", "--after", "Some text.")
        self.ok("comment", self.note, "--as", "checker", "--text", "why dog?", "--on", "2")
        ms = self.marks()
        self.assertEqual([m["kind"] for m in ms], ["comment", "substitution", "comment"])
        self.assertEqual(ms[2]["start"], ms[1]["end"])
        self.assertEqual(ms[0]["author"], "Claude (checker)")

    def test_needs_a_place(self):
        self.write("x\n")
        self.refused("comment", self.note, "--as", "checker", "--text", "hi", needle="--on N")


class Accept(Vault):
    def test_accepts_the_humans_suggestion(self):
        self.write(f"The {HUMAN_SUB} sat.\n")
        self.ok("accept", self.note, "1", "--as", "editor")
        self.assertEqual(self.read(), "The dog sat.\n")

    def test_never_an_agents_suggestion(self):
        self.write(f"The {{{EDITOR} date=\"2026-10-15\"~~cat~>dog~~}} sat.\n")
        self.refused("accept", self.note, "1", "--as", "editor", needle="only the human accepts")

    def test_not_while_a_comment_is_attached(self):
        self.write(f"The {HUMAN_SUB}{{{EDITOR} date=\"2026-10-15\">>really?<<}} sat.\n")
        self.refused("accept", self.note, "1", "--as", "editor", needle="open comment")

    def test_a_comment_is_resolved_not_accepted(self):
        self.write('x {author="Pat Example">>note<<}\n')
        self.refused("accept", self.note, "1", "--as", "editor", needle="use `resolve`")

    def test_only_the_editor(self):
        self.write(f"The {HUMAN_SUB} sat.\n")
        self.refused("accept", self.note, "1", "--as", "checker", needle="only the editor")

    def test_no_reject_command(self):
        self.write(f"The {HUMAN_SUB} sat.\n")
        code, _, err = self.run_tool("reject", self.note, "1", "--as", "editor")
        self.assertEqual(code, 2)
        self.assertIn("invalid choice", err)


class Resolve(Vault):
    def test_agents_comment_freely(self):
        self.write(f"x {{{EDITOR} date=\"2026-10-15\">>mine<<}} y\n")
        self.ok("resolve", self.note, "1", "--as", "editor")
        self.assertEqual(self.read(), "x  y\n")

    def test_humans_comment_needs_a_suggestion_addressing_it(self):
        self.write('Old wording here. {author="Pat Example">>shorter please<<}\n')
        self.refused("resolve", self.note, "1", "--as", "editor", needle="--addressed-by")
        self.ok("suggest", self.note, "--as", "editor", "--old", "Old wording here.", "--new", "Short.")
        self.ok("resolve", self.note, "2", "--as", "editor", "--addressed-by", "1")
        ms = self.marks()
        self.assertEqual([(m["kind"], m["author"]) for m in ms],
                         [("substitution", "Claude (editor)"), ("comment", "Claude (editor)")])
        self.assertIn('"shorter please"', ms[1]["text"])

    def test_addressed_by_must_be_the_editors_pending_suggestion(self):
        self.write(f'{HUMAN_SUB} {{author="Pat Example">>hm<<}}\n')
        self.refused("resolve", self.note, "2", "--as", "editor", "--addressed-by", "1", needle="not a pending suggestion")


# --- block, tidy, revise -----------------------------------------------------------------------

def accept_all(text):
    """What the human's Track Changes leaves after accepting every mark (comments dropped)."""
    out, i = [], 0
    for m in tc.parse(text):
        out.append(text[i:m["start"]])
        out.append(tc.resolve_mark(m, True))
        i = m["end"]
    return "".join(out) + text[i:]


class BlockTidyRevise(Vault):
    NOTE = "# List\n\n- alpha\n- beta and gamma\n- delta\n\nEnd.\n"

    def new_lines(self, text):
        f = os.path.join(self.d.name, "new.txt")
        with open(f, "w") as fh:
            fh.write(text)
        return f

    def test_block_then_tidy_after_accept(self):
        self.write(self.NOTE)
        self.ok("block", self.note, "--as", "editor", "--first", "beta and gamma", "--last", "beta and gamma",
                "--new-file", self.new_lines("- beta\n  - gamma\n"), "--why", "split")
        text = self.read()
        self.assertIn('- {author="Claude (editor)"', text)          # the list marker stays outside the mark
        self.assertEqual([m["kind"] for m in tc.parse(text)], ["deletion", "addition", "addition", "comment"])
        self.write(accept_all(text).replace("- \n", "\n"))          # Track Changes leaves empty lines behind
        self.assertIn("accepted, restored exactly", self.ok("tidy", self.note, "--as", "editor"))
        self.assertEqual(self.read(), "# List\n\n- alpha\n- beta\n  - gamma\n- delta\n\nEnd.\n")
        self.refused("tidy", self.note, "--as", "editor", needle="no recorded block")

    def test_tidy_leaves_a_block_with_pending_marks(self):
        self.write(self.NOTE)
        self.ok("block", self.note, "--as", "editor", "--first", "alpha", "--last", "alpha",
                "--new-file", self.new_lines("- ALPHA\n"))
        self.assertIn("still has pending marks", self.ok("tidy", self.note, "--as", "editor"))

    def test_block_refuses_lines_holding_marks(self):
        self.write(f"- {HUMAN_SUB}\n- b\n")
        self.refused("block", self.note, "--as", "editor", "--first", "Pat", "--last", "- b",
                     "--new-file", self.new_lines("- x\n"), needle="hold marks")

    def test_revise_folds_own_suggestions_into_one(self):
        self.write("The quick brown fox.\n")
        self.ok("suggest", self.note, "--as", "editor", "--old", "quick", "--new", "slow")
        self.ok("suggest", self.note, "--as", "editor", "--old", "brown", "--new", "red")
        self.ok("revise", self.note, "--as", "editor", "--marks", "1-2", "--new", "lazy grey", "--why", "one card")
        ms = self.marks()
        self.assertEqual([m["kind"] for m in ms], ["substitution", "comment"])
        self.assertEqual((ms[0]["old"], ms[0]["new"]), ("quick brown", "lazy grey"))

    def test_revise_refuses_the_humans_marks(self):
        self.write(f"The quick {HUMAN_SUB} fox.\n")
        self.ok("suggest", self.note, "--as", "editor", "--old", "quick", "--new", "slow")
        self.ok("suggest", self.note, "--as", "editor", "--old", "fox", "--new", "hen")
        self.refused("revise", self.note, "--as", "editor", "--marks", "1-3", "--new", "x", needle="only your own")

    def test_revise_bad_marks(self):
        self.write("x\n")
        self.refused("revise", self.note, "--as", "editor", "--marks", "a", "--new", "y", needle="bad --marks")


# --- the write guards ----------------------------------------------------------------------------

class Guards(Vault):
    def test_every_hold_name_refuses_every_write(self):
        self.write("Some text.\n")
        for name in tc.HOLD_NAMES:
            with self.subTest(name=name):
                hold = os.path.join(self.vault, name)
                self.write("", hold)
                err = self.refused("comment", self.note, "--as", "checker", "--text", "hi", "--after", "Some text.",
                                   needle="hold switch")
                self.assertIn(name, err)
                code, out, _ = self.run_tool("hold", self.note)
                self.assertEqual((code, out.startswith("on:")), (4, True))
                os.remove(hold)
        self.assertEqual(self.run_tool("hold", self.note)[0], 0)
        self.ok("comment", self.note, "--as", "checker", "--text", "hi", "--after", "Some text.")

    def test_hold_in_a_subfolder_and_not_above_the_vault_root(self):
        sub = os.path.join(self.vault, "sub")
        os.makedirs(sub)
        note = os.path.join(sub, "n.md")
        self.write("x\n", note)
        self.write("", os.path.join(self.home, ".track-changes-hold"))    # above the vault root: not this vault's
        self.assertEqual(tc.hold_for(note), "")
        self.write("", os.path.join(self.vault, "track-changes-hold.md"))
        self.assertTrue(tc.hold_for(note).endswith("track-changes-hold.md"))

    def test_conflict_copy(self):
        self.write("Some text.\n")
        self.write("x", os.path.join(self.vault, "note (Conflicted copy iPad 202610151200).md"))
        self.refused("comment", self.note, "--as", "checker", "--text", "hi", "--after", "Some text.",
                     needle="conflict copies")

    def test_inkling_enabled(self):
        self.write("Some text.\n")
        with open(os.path.join(self.vault, ".obsidian", "community-plugins.json"), "w") as f:
            json.dump(["obsidian-track-changes-agent", "inkling"], f)
        self.refused("comment", self.note, "--as", "checker", "--text", "hi", "--after", "Some text.",
                     needle="Inkling is enabled")

    def test_waits_for_quiet_then_gives_up(self):
        self.write("Some text.\n")
        code, _, err = self.run_tool("comment", self.note, "--as", "checker", "--text", "hi", "--after", "Some text.",
                                     env={"TRACK_CHANGES_QUIET": "30", "TRACK_CHANGES_MAX_WAIT": "1"})
        self.assertNotEqual(code, 0)
        self.assertIn("probably typing", err)

    def test_a_write_that_does_not_stick_exits_3(self):
        self.write("Some text.\n")
        env = {"TRACK_CHANGES_VERIFY_DELAY": "3"}

        def overwrite():                       # "Obsidian" saves its stale buffer over the change
            deadline = time.time() + 10
            while time.time() < deadline:
                if "Claude (checker)" in self.read():
                    self.write("Some text.\n")
                    return
                time.sleep(0.05)
        t = threading.Thread(target=overwrite)
        t.start()
        code, _, err = self.run_tool("comment", self.note, "--as", "checker", "--text", "hi", "--after", "Some text.",
                                     env=env)
        t.join()
        self.assertEqual(code, 3, err)
        self.assertIn("did not stick", err)

    def test_atomic_replace_keeps_the_mode(self):
        self.write("Some text.\n")
        os.chmod(self.note, 0o640)
        self.ok("comment", self.note, "--as", "checker", "--text", "hi", "--after", "Some text.")
        self.assertEqual(os.stat(self.note).st_mode & 0o777, 0o640)
        self.assertEqual([f for f in os.listdir(self.vault) if f.startswith(".obsidian-track-changes-agent-")], [])


# --- watch -----------------------------------------------------------------------------------------

class Watch(Vault):
    def watch(self, *extra, after=None, delay=0.6, **kw):
        """Run watch; optionally change the note `delay` seconds after it starts."""
        if after:
            threading.Timer(delay, after).start()
        return self.run_tool("watch", self.note, "--interval", "0.2", "--settle", "0.5", *extra, **kw)

    def test_timeout_then_new_human_mark_then_no_repeat(self):
        self.write("Some text.\n")
        code, out, _ = self.watch("--timeout", "1")
        self.assertEqual(code, 1)
        self.assertIn("TIMEOUT", out)
        code, out, _ = self.watch("--timeout", "10", "--json",
                                  after=lambda: self.write(f"Some {HUMAN_SUB} text.\n"))
        self.assertEqual(code, 0, out)
        items = json.loads(out)["items"]
        self.assertEqual([(i["kind"], i["author"]) for i in items], [("substitution", "Pat Example")])
        self.assertEqual(self.watch("--timeout", "1")[0], 1)          # re-armed: not reported again

    def test_agents_marks_do_not_wake_it(self):
        self.write("Some text.\n")
        self.watch("--timeout", "0.5")                                  # baseline
        code, _, _ = self.watch("--timeout", "2",
                                after=lambda: self.write(f'Some {{{EDITOR} date="2026-10-15"++new++}} text.\n'))
        self.assertEqual(code, 1)

    def test_marks_that_arrived_between_watches_are_reported(self):
        self.write("Some text.\n")
        self.watch("--timeout", "0.5")
        self.write('Some text. {author="Pat Example">>while nobody watched<<}\n')
        code, out, _ = self.watch("--timeout", "5")
        self.assertEqual(code, 0, out)
        self.assertIn("while nobody watched", out)

    def test_report_existing(self):
        self.write(f"Some {HUMAN_SUB} text.\n")
        code, out, _ = self.watch("--timeout", "5", "--report-existing")
        self.assertEqual(code, 0, out)

    def test_conflict_copy_exits_2(self):
        self.write("Some text.\n")
        self.write("x", os.path.join(self.vault, "note (Conflicted copy Mac 1).md"))
        code, out, _ = self.watch("--timeout", "5")
        self.assertEqual(code, 2)
        self.assertIn("CONFLICT", out)

    def test_folder_with_pattern(self):
        self.write("a\n", os.path.join(self.vault, "variant-a.md"))
        self.write("b\n", os.path.join(self.vault, "other.md"))
        args = ["watch", self.vault, "--pattern", "variant-*.md", "--interval", "0.2", "--settle", "0.3"]
        self.run_tool(*args, "--timeout", "0.5")
        threading.Timer(0.6, lambda: self.write('b {author="Pat Example">>x<<}\n',
                                                os.path.join(self.vault, "other.md"))).start()
        self.assertEqual(self.run_tool(*args, "--timeout", "2")[0], 1)  # other.md is not watched

    def test_nothing_to_watch(self):
        code, _, err = self.run_tool("watch", os.path.join(self.vault, "missing.md"), "--timeout", "1")
        self.assertNotEqual(code, 0)
        self.assertIn("nothing to watch", err)


# --- the earlier tool's state carries over ---------------------------------------------------

class LegacyState(Vault):
    def test_block_records_and_watch_baselines_are_read_from_the_old_folder(self):
        legacy = os.path.join(self.home, ".local", "state", "criticmarkup")
        os.makedirs(legacy)
        self.write("# L\n\n- a\n- b\n\nEnd.\n")
        record = {"file": os.path.realpath(self.note), "id": "b1", "above": "- a", "below": "End.",
                  "rejected": ["- b", ""], "accepted": ["- B", ""]}
        with open(os.path.join(legacy, "blocks.json"), "w") as f:
            json.dump([record], f)
        self.write("# L\n\n- a\n- B\n\n\nEnd.\n")
        out = self.ok("tidy", self.note, "--as", "editor", drop=("TRACK_CHANGES_STATE",))
        self.assertIn("accepted, restored exactly", out)
        self.assertEqual(self.read(), "# L\n\n- a\n- B\n\nEnd.\n")
        new_state = os.path.join(self.home, ".local", "state", "track-changes", "blocks.json")   # name kept on purpose
        with open(new_state) as f:
            self.assertEqual(json.load(f), [])                           # written to the new folder

    def test_an_explicit_state_path_ignores_the_old_folder(self):
        legacy = os.path.join(self.home, ".local", "state", "criticmarkup")
        os.makedirs(legacy)
        self.write("x\n")
        with open(os.path.join(legacy, "blocks.json"), "w") as f:
            json.dump([{"file": os.path.realpath(self.note), "id": "b1", "above": None, "below": None,
                        "rejected": ["x"], "accepted": ["x"]}], f)
        self.refused("tidy", self.note, "--as", "editor", needle="no recorded block")

    def test_legacy_environment_names(self):
        self.write("Some text.\n")
        env = {"CRITICMARKUP_QUIET": "0", "CRITICMARKUP_VERIFY_DELAY": "0"}
        self.ok("comment", self.note, "--as", "checker", "--text", "hi", "--after", "Some text.",
                env=env, drop=("TRACK_CHANGES_QUIET", "TRACK_CHANGES_VERIFY_DELAY"))


# --- install-links ---------------------------------------------------------------------------------

class InstallLinks(Vault):
    def setUp(self):
        super().setUp()
        self.install = os.path.join(self.d.name, "cache", "obsidian-track-changes-agent", "0.1.0")
        os.makedirs(os.path.join(self.install, "bin"))
        shutil.copy2(TOOL, os.path.join(self.install, "bin", "obsidian-track-changes-agent"))
        self.plugins = os.path.join(self.d.name, "installed_plugins.json")
        self.set_plugins({"obsidian-track-changes-agent@example": [{"scope": "user", "installPath": self.install,
                                                       "version": "0.1.0"}]})
        self.bin = os.path.join(self.d.name, "bin")
        self.link = os.path.join(self.bin, "obsidian-track-changes-agent")
        self.env["TRACK_CHANGES_PLUGINS_FILE"] = self.plugins

    def set_plugins(self, plugins):
        with open(self.plugins, "w") as f:
            json.dump({"version": 2, "plugins": plugins}, f)

    def links(self, *extra):
        return self.run_tool("install-links", "--bin-dir", self.bin, *extra)

    def test_create_ok_check_repoint(self):
        self.assertEqual(self.links("--check")[0], 1)
        code, out, _ = self.links("--dry-run")
        self.assertEqual(code, 0)
        self.assertFalse(os.path.lexists(self.link))
        code, out, _ = self.links()
        self.assertEqual(code, 0, out)
        self.assertEqual(os.path.realpath(self.link), os.path.realpath(os.path.join(self.install, "bin", "obsidian-track-changes-agent")))
        self.assertIn("ok", self.links()[1])
        self.assertEqual(self.links("--check")[0], 0)
        code, out, _ = self.run_tool("install-links", "--bin-dir", self.bin, "--dev", ROOT)
        self.assertEqual(code, 0, out)
        self.assertIn("was", out)
        self.assertEqual(os.path.realpath(self.link), os.path.realpath(TOOL))
        p = subprocess.run([self.link, "--version"], capture_output=True, text=True)
        self.assertEqual(p.stdout.strip(), f"obsidian-track-changes-agent {tc.VERSION}")
        self.assertFalse(os.path.lexists(os.path.join(self.bin, "track-changes")))   # alias dropped in 0.1.3

    def test_blocked_by_a_file_unless_forced(self):
        os.makedirs(self.bin)
        self.write("not a link", self.link)
        code, out, _ = self.links()
        self.assertEqual(code, 1)
        self.assertIn("refused", out)
        self.assertEqual(self.links("--force")[0], 0)
        self.assertTrue(os.path.islink(self.link))

    def test_reads_the_claude_config_dir(self):
        config = os.path.join(self.d.name, "config")
        os.makedirs(os.path.join(config, "plugins"))
        shutil.copy(self.plugins, os.path.join(config, "plugins", "installed_plugins.json"))
        code, out, err = self.run_tool("install-links", "--bin-dir", self.bin, env={"CLAUDE_CONFIG_DIR": config},
                                       drop=("TRACK_CHANGES_PLUGINS_FILE",))
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.islink(self.link))

    def test_no_install_and_two_installs(self):
        self.set_plugins({})
        code, _, err = self.links()
        self.assertNotEqual(code, 0)
        self.assertIn("install the plugin first", err)
        entry = [{"scope": "user", "installPath": self.install, "version": "0.1.0"}]
        self.set_plugins({"obsidian-track-changes-agent@a": entry, "obsidian-track-changes-agent@b": entry, "other@a": entry})
        code, _, err = self.links()
        self.assertIn("more than one", err)
        self.assertEqual(self.links("--from", "obsidian-track-changes-agent@b")[0], 0)


# --- the session-start Python check -----------------------------------------------------------------

HOOK = os.path.join(os.path.dirname(os.path.dirname(TOOL)), "hooks", "check-python.sh")


@unittest.skipUnless(os.path.isfile(HOOK), "no hooks/check-python.sh")
class PythonCheck(unittest.TestCase):
    def test_silent_when_python3_is_there(self):
        p = subprocess.run(["/bin/sh", HOOK], capture_output=True, text=True,
                           env={"PATH": os.path.dirname(sys.executable) + ":/usr/bin:/bin"})
        if os.path.realpath(sys.executable).startswith("/usr/bin") and sys.platform == "darwin":
            self.skipTest("system python on macOS: the check depends on the Command Line Tools")
        self.assertEqual((p.returncode, p.stdout), (0, ""))

    def test_says_so_when_python3_is_missing(self):
        with tempfile.TemporaryDirectory() as d:
            for tool in ("uname", "xcode-select"):
                real = shutil.which(tool)
                if real:
                    os.symlink(real, os.path.join(d, tool))
            p = subprocess.run(["/bin/sh", HOOK], capture_output=True, text=True, env={"PATH": d})
        out = json.loads(p.stdout)
        self.assertIn("needs Python 3", out["systemMessage"])
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")


if __name__ == "__main__":
    unittest.main(verbosity=1)
