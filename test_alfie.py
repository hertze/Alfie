"""Tests for Alfie. Run them with:  python3 -m unittest -v

The Swedish calendar is checked for every year Alfie accepts (2005-9998) against a second,
separate implementation written straight from the wording of Lag (1989:253) om allmänna
helgdagar, which steps through the calendar day by day instead of doing date arithmetic.
Easter is checked against two other published algorithms for every Gregorian year from
1583, and against dates from published tables."""

import contextlib
import io
import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import alfie

ONE = timedelta(days=1)
MON, TUE, WED, THU, FRI, SAT, SUN = range(7)


# --- A second implementation, kept apart from alfie.py on purpose -----------------------

def easter_knuth(y):
    """Knuth, The Art of Computer Programming, vol. 1, 1.3.2 exercise 14 (Gregorian)."""
    g = y % 19 + 1
    c = y // 100 + 1
    x = 3 * c // 4 - 12
    z = (8 * c + 5) // 25 - 5
    d = 5 * y // 4 - x - 10
    e = (11 * g + 20 + z - x) % 30
    if (e == 25 and g > 11) or e == 24:
        e += 1
    n = 44 - e
    if n < 21:
        n += 30
    n = n + 7 - (d + n) % 7
    return date(y, 4, n - 31) if n > 31 else date(y, 3, n)


def easter_gauss(y):
    """Gauss's Easter formula in Lichtenberg's corrected form."""
    k = y // 100
    m = 15 + (3 * k + 3) // 4 - (8 * k + 13) // 25
    s = 2 - (3 * k + 3) // 4
    a = y % 19
    d = (19 * a + m) % 30
    r = (d + a // 11) // 29
    og = 21 + d - r
    sz = 7 - (y + y // 4 + s) % 7
    oe = 7 - (og - sz) % 7
    return date(y, 3, 1) + timedelta(days=og + oe - 1)


def nth_after(start, weekday, n):
    day, count = start, 0
    while True:
        day += ONE
        if day.weekday() == weekday:
            count += 1
            if count == n:
                return day


def nearest_before(start, weekday):
    day = start - ONE
    while day.weekday() != weekday:
        day -= ONE
    return day


def only(first, last, weekday):
    days = [first + timedelta(days=i) for i in range((last - first).days + 1)]
    hits = [day for day in days if day.weekday() == weekday]
    assert len(hits) == 1
    return hits[0]


def weekdays_in(y, month, weekday):
    day, hits = date(y, month, 1), []
    while day.month == month:
        if day.weekday() == weekday:
            hits.append(day)
        day += ONE
    return hits


def law_calendar(y):
    """Every built-in day, from the wording of the law (red days) and the usual rules."""
    easter = easter_knuth(y)
    midsummer = only(date(y, 6, 20), date(y, 6, 26), SAT)
    return {
        (date(y, 1, 1), "Nyårsdagen", True),
        (date(y, 1, 6), "Trettondedag jul", True),
        (nearest_before(easter, FRI), "Långfredagen", True),       # fredagen närmast före påskdagen
        (easter, "Påskdagen", True),
        (easter + ONE, "Annandag påsk", True),                    # dagen efter påskdagen
        (date(y, 5, 1), "Första maj", True),
        (nth_after(easter, THU, 6), "Kristi himmelsfärd", True),  # sjätte torsdagen efter påskdagen
        (nth_after(easter, SUN, 7), "Pingstdagen", True),         # sjunde söndagen efter påskdagen
        (date(y, 6, 6), "Nationaldagen", True),
        (midsummer, "Midsommardagen", True),                      # lördagen 20-26 juni
        (only(date(y, 10, 31), date(y, 11, 6), SAT), "Alla helgons dag", True),  # lördagen 31 okt-6 nov
        (date(y, 12, 25), "Juldagen", True),
        (date(y, 12, 26), "Annandag jul", True),
        (date(y, 2, 14), "Alla hjärtans dag", False),
        (nearest_before(easter, THU), "Skärtorsdagen", False),
        (nearest_before(easter, SAT), "Påskafton", False),
        (nth_after(easter, SUN, 7) + ONE, "Annandag pingst", False),
        (weekdays_in(y, 5, SUN)[-1], "Mors dag", False),          # sista söndagen i maj
        (midsummer - ONE, "Midsommarafton", False),
        (date(y, 10, 31), "Halloween", False),
        (weekdays_in(y, 11, SUN)[1], "Fars dag", False),          # andra söndagen i november
        (date(y, 12, 13), "Lucia", False),
        (date(y, 12, 24), "Julafton", False),
        (date(y, 12, 31), "Nyårsafton", False),
        (weekdays_in(y, 3, SUN)[-1], "sommartid börjar", False),  # EU: sista söndagen i mars
        (weekdays_in(y, 10, SUN)[-1], "vintertid börjar", False),  # EU: sista söndagen i oktober
    }


# --- Tests ---------------------------------------------------------------------------------

class SwedishCalendarTest(unittest.TestCase):
    def test_easter_agrees_with_two_other_algorithms_1583_to_9998(self):
        for year in range(1583, 9999):
            self.assertEqual(alfie.easter_sunday(year), easter_knuth(year), year)
            self.assertEqual(alfie.easter_sunday(year), easter_gauss(year), year)

    def test_easter_matches_published_dates(self):
        published = [date(1943, 4, 25), date(2008, 3, 23), date(2019, 4, 21),
                     date(2024, 3, 31), date(2025, 4, 20), date(2026, 4, 5), date(2027, 3, 28),
                     date(2028, 4, 16), date(2038, 4, 25), date(2049, 4, 18), date(2076, 4, 19),
                     date(2285, 3, 22)]
        for day in published:
            self.assertEqual(alfie.easter_sunday(day.year), day)

    def test_every_built_in_day_follows_the_law_2005_to_9998(self):
        for year in range(alfie.FIRST_SWEDISH_YEAR, 9999):
            self.assertEqual(set(alfie.swedish_calendar(year)), law_calendar(year), year)

    def test_thirteen_red_days_every_year(self):
        for year in range(alfie.FIRST_SWEDISH_YEAR, 9999):
            self.assertEqual(sum(red for _, _, red in alfie.swedish_calendar(year)), 13, year)

    def test_2027_weekday_red_days_match_uppsala_university(self):
        # uu.se, "Röda dagar och klämdagar 2027" (updated 21 October 2026)
        expected = {date(2027, 1, 1), date(2027, 1, 6), date(2027, 3, 26), date(2027, 3, 29), date(2027, 5, 6)}
        ours = {day for day, _, red in alfie.swedish_calendar(2027) if red and day.weekday() < SAT}
        self.assertEqual(ours, expected)

    def test_years_before_2005_are_refused(self):
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(alfie.make_diary(alfie.Settings(year=2004), Path(folder)), 1)


class WordsTest(unittest.TestCase):
    def parse(self, line):
        return alfie.parse_words(line.split(), alfie.Settings())

    def test_words_in_any_order(self):
        command, settings, _ = self.parse("save-paper 2028 Pocket wg color")
        self.assertIsNone(command)
        self.assertEqual((settings.year, settings.paper, settings.layout, settings.color, settings.save_paper),
                         (2028, "pocket", "wg", "color", True))

    def test_commands_and_their_short_forms(self):
        self.assertEqual(self.parse("list 2027")[0], "list")
        self.assertEqual(self.parse("h")[0], "help")
        self.assertEqual(self.parse("exit")[0], "quit")

    def test_old_flags_still_work(self):
        command, settings, _ = self.parse("2027 --paper pocket --save-paper --list --holidays none")
        self.assertEqual(command, "list")
        self.assertEqual((settings.paper, settings.save_paper, settings.calendar), ("pocket", True, "none"))

    def test_a_setting_name_on_its_own_is_reported(self):
        self.assertEqual(self.parse("layout")[2], ["layout"])

    def test_mistakes_are_explained(self):
        for line, expected in [("pockt", "Did you mean pocket?"),
                               ("make list", "One command at a time"),
                               ("27", "isn't a year"),
                               ("personal-color-w2p-sv-2014-yes", "personal color w2p sv 2014"),
                               ("banana", "help shows them all")]:
            with self.assertRaises(alfie.WordError) as caught:
                self.parse(line)
            self.assertIn(expected, str(caught.exception))

    def test_words_for_settings_leave_out_the_usual_ones(self):
        settings = alfie.Settings(year=2028, paper="pocket", save_paper=True)
        self.assertEqual(settings.words(), ["2028", "pocket", "save-paper"])
        self.assertEqual(alfie.parse_words(settings.words(), alfie.Settings())[1], settings)


class ShellTest(unittest.TestCase):
    def run_shell(self, lines):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch("builtins.input", side_effect=lines), contextlib.redirect_stdout(output):
            Path(folder, "dates.md").write_text("25 mars: Daniels födelsedag\n", encoding="utf-8")
            status = alfie.shell(Path(folder))
        return status, output.getvalue()

    def test_settings_stay_between_lines(self):
        status, output = self.run_shell(["personal", "pocket 2035", "save-paper", "layout", "pockt", "list", "quit"])
        self.assertEqual(status, 0)
        self.assertIn("  Year       2035\n  Paper      pocket    83 × 122 mm\n", output)  # only what changed
        self.assertIn("  Save paper on        4 pages on each A4 sheet\n", output)
        self.assertIn("Layouts:", output)
        self.assertIn("Did you mean pocket?", output)
        self.assertIn("Using the Swedish calendar and dates.md (1 every year, 0 for 2035 only).", output)
        self.assertIn("Red days (●) and notes for 2035.", output)

    def test_help_in_the_shell_marks_the_current_values(self):
        output = self.run_shell(["pocket save-paper", "help", "quit"])[1]
        self.assertIn("  Paper       pocket*  personal  a6  a5\n", output)
        self.assertIn("  Save paper  save-paper*  no-save-paper\n", output)
        self.assertIn("  settings    show all the settings\n", output)

    def test_a_leading_alfie_is_fine(self):
        output = self.run_shell(["alfie a6", "quit"])[1]
        self.assertIn("  Paper      a6        107 × 150 mm\n", output)

    def test_end_of_input_leaves_the_shell(self):
        self.assertEqual(self.run_shell([EOFError()])[0], 0)


class SettingsTableTest(unittest.TestCase):
    usual = dict(year=2035, paper="personal", layout="w2pwf", language="sv", color="bw", save_paper=False,
                 back_offset=1.0)

    def test_the_whole_table(self):
        table = alfie.settings_table(alfie.Settings(**self.usual))
        self.assertEqual(table.splitlines(), [
            "  Year       2035",
            "  Paper      personal  97 × 173 mm",
            "  Layout     w2pwf     a week on two pages, with more room for the weekdays",
            "  Language   sv        Swedish",
            "  Colour     bw        black and white",
            "  Save paper off       one page per A4 sheet",
            "  Back side  +1.0 mm   the back of each sheet moved 1 mm down",
            "  Holidays   on        the Swedish calendar",
        ])
        with_output = alfie.settings_table(alfie.Settings(**self.usual, tex_only=True))
        self.assertIn("  Output     tex-only  only the LaTeX file", with_output)

    def test_only_the_lines_that_changed(self):
        before = alfie.Settings(**self.usual)
        after = alfie.Settings(**{**self.usual, "paper": "a5", "language": "en", "save_paper": True})
        self.assertEqual(alfie.settings_table(after, before).splitlines(), [
            "  Paper      a5        150 × 212 mm",
            "  Language   en        English",
            "  Save paper on        but only one a5 page fits on an A4 sheet",
            "  Holidays   off       only Sundays are red",
        ])


class BackSideTest(unittest.TestCase):
    def test_words(self):
        for word, value in [("back=+0.9", 0.9), ("back=0", 0.0), ("back-0.5", -0.5), ("back+1,2", 1.2),
                            ("--back=1", 1.0)]:
            self.assertEqual(alfie.parse_words([word], alfie.Settings())[1].back_offset, value, word)
        with self.assertRaises(alfie.WordError):
            alfie.parse_words(["back=25"], alfie.Settings())
        self.assertEqual(alfie.parse_words(["back"], alfie.Settings())[2], ["back"])

    def test_how_offsets_are_written(self):
        self.assertEqual([alfie.signed_mm(value) for value in (1.0, 0.9, -0.5, 0.95, 0)],
                         ["+1.0", "+0.9", "-0.5", "+0.95", "0"])

    def test_paper_saving_moves_only_the_backs_down(self):
        layout = alfie.sheet_layout("pocket")
        plain, moved = alfie.sheet_plan(layout, 107), alfie.sheet_plan(layout, 107, back_offset=0.9)
        for number, (before, after) in enumerate(zip(plain, moved)):
            shift = 0.9 if number % 2 else 0.0  # every second side is a back
            for p, q in zip(before, after):
                self.assertEqual((q.box[0], q.box[2]), (p.box[0], p.box[2]))
                self.assertAlmostEqual(p.box[1] - q.box[1], shift)
                self.assertAlmostEqual(p.box[3] - q.box[3], shift)

    def test_one_page_per_sheet_moves_the_backs_only_when_asked(self):
        diary = alfie.Diary(2027, "personal", "bw", "w2pwf", "sv", alfie.Notes({}, {}, []))
        self.assertNotIn("AlfieSide", diary.latex())
        self.assertIn("\\AlfieFrontVoffset+0.90mm", diary.latex(back_offset=0.9))
        self.assertIn("\\AlfieFrontVoffset+-0.50mm", diary.latex(back_offset=-0.5))
        self.assertNotIn("AlfieSide", diary.latex(trimmed=True, back_offset=0.9))  # the sheets move them


def arguments(latex, command, count):
    """The {...} arguments of every use of a LaTeX command, as lists of strings."""
    found, start = [], latex.find(command + "{")
    while start != -1:
        args, pos = [], start + len(command)
        for _ in range(count):
            depth, begin = 0, pos
            while True:
                if latex[pos] == "\\":
                    pos += 2  # an escaped brace, \{ or \}, doesn't count
                    continue
                depth += {"{": 1, "}": -1}.get(latex[pos], 0)
                pos += 1
                if depth == 0:
                    break
            args.append(latex[begin + 1:pos - 1])
        found.append(args)
        start = latex.find(command + "{", pos)
    return found


class ColumnLayoutTest(unittest.TestCase):
    def diary(self, layout="w2pcolslandscape", paper="personal", days=None):
        return alfie.Diary(2027, paper, "bw", layout, "sv", alfie.Notes(days or {}, {}, []))

    def test_monday_to_wednesday_on_the_left_thursday_to_sunday_on_the_right(self):
        for layout in alfie.COLUMN_LAYOUTS:  # turned, the left-hand page is above the rings
            diary = self.diary(layout)
            pages = arguments(diary.latex(), "\\AlfieWeekPage", 4)
            self.assertEqual(len(pages), 2 * len(diary.weeks()))
            left, right = pages[4], pages[5]  # the third week, week 2: 11-17 januari
            for header in (left[0], right[0]):
                self.assertIn("januari 2027", header)
                self.assertIn("vecka 2", header)  # on both pages, as in the sketch
            for column, (date, weekday) in zip(left[1:] + right[1:3],
                                               [(11, "måndag"), (12, "tisdag"), (13, "onsdag"),
                                                (14, "torsdag"), (15, "fredag")]):
                self.assertIn(f"{{{date}}}", column)
                self.assertIn(weekday, column)
            weekend = right[3]
            saturday, line, sunday = (weekend.index(text) for text in ("lördag", "{0.1pt}", "söndag"))
            self.assertLess(saturday, line)
            self.assertLess(line, sunday)

    def test_notes_are_escaped_and_may_go_under_the_date(self):
        days = {date(2027, 1, 12): alfie.DayInfo(entries=[(1, 0, "Tandläkare 08.30 & frisör")])}
        note = "\\small \\notescolor{Tandläkare 08.30 \\& frisör}"
        turned = self.diary(days=days).latex()  # beside the weekday if there's room
        self.assertEqual(arguments(turned, "\\AlfieDay", 2)[0][1], note)
        upright = self.diary("w2pcolsportrait", days=days).latex()  # always under, flush left
        self.assertNotIn("\\AlfieDay{", upright)
        self.assertEqual(arguments(upright, "\\AlfieNoteUnder", 1), [[note]])
        self.assertIn("tisdag\n\n\\AlfieNoteUnder", upright)

    def test_turned_pages_get_the_outer_margin_at_both_ends(self):
        for paper, size in alfie.PAPERS.items():
            turned = self.diary(paper=paper).preamble()
            self.assertIn(f"bottom={size['margin']}mm, top={size['margin']}mm", turned)
            self.assertIn(f"\\setlength\\AlfieGap{{{size['margin']}mm}}", turned)
            self.assertIn("\\rotatebox{90}", turned)

    def test_upright_pages_keep_the_usual_margins(self):
        for paper, size in alfie.PAPERS.items():
            for layout in ("w2pcolsportrait", "w2pwf"):
                self.assertIn(f"bottom={size['bottom']}mm, top={size['top']}mm", self.diary(layout, paper).preamble())
            upright = self.diary("w2pcolsportrait", paper).preamble()
            self.assertIn("\\setlength\\AlfieGap{2mm}", upright)  # narrow columns: less space beside the lines
            self.assertNotIn("rotatebox{90}", upright)

    def test_only_the_turned_layout_turns_its_title_page(self):
        turned = self.diary().latex()
        self.assertNotIn("\\maketitle", turned)
        self.assertIn("\\AlfiePage{\\centering", turned)
        self.assertIn("Året 2027", turned)
        self.assertIn("\\maketitle", self.diary("w2pcolsportrait").latex())

    def test_other_layouts_are_unchanged(self):
        self.assertLessEqual(alfie.TURNED_LAYOUTS, alfie.COLUMN_LAYOUTS)
        self.assertLessEqual(alfie.COLUMN_LAYOUTS, set(alfie.LAYOUTS))
        for layout in set(alfie.LAYOUTS) - alfie.COLUMN_LAYOUTS:
            self.assertNotIn("\\AlfiePage", self.diary(layout).latex(), layout)


class InstallTest(unittest.TestCase):
    def test_links_alfie_into_a_folder_on_path(self):
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            folder = Path(folder).resolve()
            with mock.patch.dict(os.environ, {"PATH": str(folder)}):
                self.assertEqual(alfie.install([Path("/nonexistent"), folder]), 0)
                self.assertEqual((folder / "alfie").resolve(), Path(alfie.__file__).resolve())
                self.assertEqual(alfie.install([folder]), 0)  # already there: fine

    def test_leaves_another_alfie_alone(self):
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stderr(io.StringIO()):
            folder = Path(folder).resolve()
            (folder / "alfie").write_text("someone else's")
            with mock.patch.dict(os.environ, {"PATH": str(folder)}):
                self.assertEqual(alfie.install([folder]), 1)
            self.assertEqual((folder / "alfie").read_text(), "someone else's")


class ListTest(unittest.TestCase):
    def test_ordinary_sundays_are_not_marked_but_sunday_holidays_are(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "dates.txt").write_text("5 september: Fars födelsedag\n", encoding="utf-8")
            notes = alfie.load_notes(2027, "se", Path(folder))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            alfie.Diary(2027, "personal", "bw", "w2pwf", "sv", notes).print_list()
        lines = output.getvalue().splitlines()
        self.assertIn("  5 sep sön    Fars födelsedag", lines)     # a Sunday, but not a holiday
        self.assertIn(" 31 okt sön    Halloween, vintertid börjar", lines)
        self.assertIn("  6 jun sön  ● Nationaldagen", lines)       # a Sunday and a holiday


class CleanUpTest(unittest.TestCase):
    def test_only_the_final_pdf_is_left(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            build = folder / "build"
            build.mkdir()
            name = "diary-personal-2027-sv"
            for suffix in (".tex", ".aux", ".log", ".out", ".pdf"):
                (build / f"{name}-pages{suffix}").write_text("x")
                (build / f"{name}-2up{suffix}").write_text("x")
            final = folder / f"{name}-2up.pdf"
            final.write_text("pdf")
            alfie.remove_build_files(build, name, keep=final)
            self.assertFalse(build.exists())
            self.assertEqual(sorted(path.name for path in folder.iterdir()), [final.name])

    def test_other_files_in_build_are_left_alone(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            build = folder / "build"
            build.mkdir()
            (build / "diary-pocket-2027-sv.log").write_text("someone else's")
            (build / "diary-personal-2027-sv.log").write_text("x")
            alfie.remove_build_files(build, "diary-personal-2027-sv", keep=folder / "diary-personal-2027-sv.pdf")
            self.assertEqual([path.name for path in build.iterdir()], ["diary-pocket-2027-sv.log"])


class SavePaperTest(unittest.TestCase):
    def test_how_many_pages_fit_on_a_sheet(self):
        self.assertEqual(alfie.sheet_layout("pocket"), alfie.SheetLayout(2, 2, False, 83.0, 122.0))
        self.assertEqual(alfie.sheet_layout("personal"), alfie.SheetLayout(1, 2, True, 173.0, 97.0))
        self.assertEqual(alfie.sheet_layout("a6"), alfie.SheetLayout(1, 2, True, 150.0, 107.0))
        self.assertIsNone(alfie.sheet_layout("a5"))

    def test_pages_fit_on_the_sheet_with_room_for_crop_marks(self):
        for paper in ("pocket", "personal", "a6"):
            layout = alfie.sheet_layout(paper)
            for place in alfie.sheet_plan(layout, 107)[0]:
                left, bottom, right, top = place.box
                self.assertGreaterEqual(min(left, bottom), alfie.SHEET_MARGIN)
                self.assertLessEqual(right, alfie.SHEET_WIDTH - alfie.SHEET_MARGIN)
                self.assertLessEqual(top, alfie.SHEET_HEIGHT - alfie.SHEET_MARGIN)

    def test_crosses_only_run_along_cutting_lines(self):
        for paper in ("pocket", "personal", "a6"):
            layout = alfie.sheet_layout(paper)
            boxes = [place.box for place in alfie.sheet_plan(layout, 107)[0]]
            for box in boxes:
                for (x1, y1), (x2, y2) in alfie.cross_lines(box):
                    self.assertTrue(x1 in (box[0] - 20, box[2] - 20, box[0], box[2]) or y1 == y2)
                    for left, bottom, right, top in boxes:  # never through the inside of a page
                        if y1 == y2:
                            inside = bottom < y1 < top and min(x2, right) > max(x1, left)
                        else:
                            inside = left < x1 < right and min(y2, top) > max(y1, bottom)
                        self.assertFalse(inside, (paper, box, (x1, y1, x2, y2)))

    def test_labels_stay_clear_of_the_crosses(self):
        for paper in ("pocket", "personal", "a6"):
            layout = alfie.sheet_layout(paper)
            left, right = alfie.label_span(layout)
            self.assertGreater(right - left, 60)
            for box in (place.box for place in alfie.sheet_plan(layout, 107)[0]):
                self.assertFalse(left < box[0] < right or left < box[2] < right)

    def test_every_page_once_and_each_back_behind_its_front(self):
        for paper in ("pocket", "personal", "a6"):
            layout = alfie.sheet_layout(paper)
            for page_count in (1, 2, 3, 7, 106, 107, 108, 213):
                sides = alfie.sheet_plan(layout, page_count)
                pages = sorted(place.page for side in sides for place in side)
                self.assertEqual(pages, list(range(1, page_count + 1)))
                for front, back in zip(sides[0::2], sides[1::2]):
                    fronts = {place.slot: place for place in front}
                    for place in back:
                        mate = fronts[place.slot]
                        self.assertEqual(place.page, mate.page + 1)       # back of the same leaf
                        l, b, r, t = mate.box                            # flipped on the long edge:
                        self.assertEqual(place.box, (alfie.SHEET_WIDTH - r, b, alfie.SHEET_WIDTH - l, t))
                        self.assertEqual(place.angle, -mate.angle)       # tops at the same edge

    def test_cut_and_stack_gives_the_leaves_in_order(self):
        for paper in ("pocket", "personal", "a6"):
            layout = alfie.sheet_layout(paper)
            for page_count in (107, 108, 213, 214):
                fronts = alfie.sheet_plan(layout, page_count)[0::2]
                piles = [[place.page for side in fronts for place in side if place.slot == slot]
                         for slot in range(layout.per_side)]
                stacked = [page for pile in piles for page in pile]
                self.assertEqual(stacked, list(range(1, page_count + 1, 2)))


if __name__ == "__main__":
    unittest.main()
