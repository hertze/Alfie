"""Tests for Alfie. Run them with:  python3 -m unittest -v

The Swedish calendar is checked for every year Alfie accepts (2005-9998) against a second,
separate implementation written straight from the wording of Lag (1989:253) om allmänna
helgdagar, which steps through the calendar day by day instead of doing date arithmetic.
Easter is checked against two other published algorithms for every Gregorian year from
1583, and against dates from published tables."""

import contextlib
import io
import tempfile
import unittest
from argparse import Namespace
from datetime import date, timedelta
from pathlib import Path

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
        args = Namespace(year=2004, language="sv", holidays=None, init=False)
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(alfie.make_diary(args, Path(folder)), 1)


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
