#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# A L F I E
# version 3.0
#
# by Joakim Hertze
#
# Makes diary inserts for ring binders as LaTeX and typesets them with XeLaTeX.
#
#   alfie 2027                     the 2027 diary, with the defaults below
#   alfie 2027 pocket save-paper   pocket size, four pages on each A4 sheet
#   alfie list 2027                the red days and notes it will show
#   alfie                          a shell, where you type the same words
#   alfie help                     all the words
#
# Until you've run ./alfie.py install, type ./alfie.py instead of alfie.

from __future__ import annotations

import calendar
import difflib
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

# What Alfie makes when you don't say otherwise.
DEFAULTS = {
    "paper": "personal",  # pocket, personal, a6 or a5
    "color": "bw",        # bw or color
    "layout": "w2pwf",    # one of LAYOUTS below
    "language": "sv",     # sv, de or en
    "save_paper": False,  # True: 2 or 4 pages on each A4 sheet (the word save-paper)
    "back_offset": 1.0,   # mm the back of each sheet is moved down, for a printer that prints
                          # the back side higher than the front (the word back=+1.0)
}
AUTHOR = "Joakim Hertze"

# Files Alfie reads from the folder you run it in, as .md or .txt (if both are
# there, the .md one is used). Lines under a heading with a year ("## 2027") are
# for that year only; all others come back every year.
DATES_FILES = ("dates.md", "dates.txt")              # your dates
WEEKNOTES_FILES = ("weeknotes.md", "weeknotes.txt")  # week notes for layout wg

# The PDF ends up in the folder you run Alfie in. LaTeX works in this subfolder, which is
# removed again after a successful run; it's left when XeLaTeX fails, so the log can be read.
BUILD_DIR = "build"

LAYOUTS = {
    "w1p": "a week on one page",
    "w1pnotes": "a week on one page, with a notes page after it",
    "w2p": "a week on two pages",
    "w2pwf": "a week on two pages, with more room for the weekdays",
    "1dp": "a day per page",
    "wg": "a week on four pages, with week dots, week notes and a gratitude page",
    "w2pcolslandscape": "a week on two pages in columns, for a binder turned on its side",
    "w2pcolsportrait": "a week on two pages in columns, for a binder held upright",
}

# Layouts with the days side by side in columns.
COLUMN_LAYOUTS = {"w2pcolslandscape", "w2pcolsportrait"}

# Layouts for a binder turned a quarter turn clockwise, so the rings run across the middle.
# Each page is laid out across and printed turned: the left-hand page then reads above the
# rings and the right-hand page below them.
TURNED_LAYOUTS = {"w2pcolslandscape"}

PAPERS = {  # millimetres
    "pocket": {"width": "83", "height": "122", "margin": "3", "left": "13", "top": "1", "bottom": "4"},
    "personal": {"width": "97", "height": "173", "margin": "3", "left": "11", "top": "2", "bottom": "3.5"},
    "a6": {"width": "107", "height": "150", "margin": "4", "left": "13", "top": "2", "bottom": "3.5"},
    "a5": {"width": "150", "height": "212", "margin": "5.5", "left": "13.5", "top": "5.5", "bottom": "10"},
}

LANGUAGES = {
    "sv": {
        "babel": "swedish",
        "days": ["måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag", "söndag"],
        "months": ["januari", "februari", "mars", "april", "maj", "juni",
                   "juli", "augusti", "september", "oktober", "november", "december"],
        "this_week": "denna vecka",
        "week": "vecka",
        "by": "av",
        "notes": "anteckningar",
        "the_year": "Året",
        "title": "för {paper}",
        "gratitude": "Vad har du känt tacksamhet över denna vecka?",
    },
    "de": {
        "babel": "german",
        "days": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
        "months": ["Januar", "Februar", "März", "April", "Mai", "Juni",
                   "Juli", "August", "September", "Oktober", "November", "Dezember"],
        "this_week": "Diese Woche",
        "week": "Woche",
        "by": "von",
        "notes": "Notizen",
        "the_year": "Das Jahr",
        "title": "für {paper} Size",
        "gratitude": "Wofür warst Du diese Woche dankbar?",
    },
    "en": {
        "babel": "english",
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        "months": ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"],
        "this_week": "this week",
        "week": "week",
        "by": "by",
        "notes": "notes",
        "the_year": "The Year",
        "title": "for {paper} Size",
        "gratitude": "What have you felt grateful for this week?",
    },
}

# ---------------------------------------------------------------------------
# Built-in calendar: red days and named days, worked out for any year
# ---------------------------------------------------------------------------

MON, TUE, WED, THU, FRI, SAT, SUN = range(7)


def easter_sunday(year):
    """Easter Sunday in the Gregorian calendar (the anonymous Gregorian algorithm)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def first_on_or_after(day, weekday):
    """The first MON..SUN on or after a date."""
    return day + timedelta(days=(weekday - day.weekday()) % 7)


def last_in_month(year, month, weekday):
    """The last MON..SUN of a month."""
    first_of_next_month = date(year + month // 12, month % 12 + 1, 1)
    return first_on_or_after(first_of_next_month - timedelta(days=7), weekday)


def swedish_calendar(year):
    """(date, name, red day?) for one year.

    The red days follow Lag (1989:253) om allmänna helgdagar as amended by SFS 2004:1320,
    in force since 2005. Easter uses the ecclesiastical (Gregorian) full moon, as the law's
    preparatory work says (prop. 1988/89:114). test_alfie.py checks every year from 2005 to
    9998 against a separate implementation of the law's wording. The named days that aren't
    red can be changed freely; the red days must stay as the law says."""
    easter = easter_sunday(year)
    midsummer = first_on_or_after(date(year, 6, 20), SAT)
    return [
        # Red days
        (date(year, 1, 1), "Nyårsdagen", True),
        (date(year, 1, 6), "Trettondedag jul", True),
        (easter - timedelta(days=2), "Långfredagen", True),
        (easter, "Påskdagen", True),
        (easter + timedelta(days=1), "Annandag påsk", True),
        (date(year, 5, 1), "Första maj", True),
        (easter + timedelta(days=39), "Kristi himmelsfärd", True),
        (easter + timedelta(days=49), "Pingstdagen", True),
        (date(year, 6, 6), "Nationaldagen", True),
        (midsummer, "Midsommardagen", True),
        (first_on_or_after(date(year, 10, 31), SAT), "Alla helgons dag", True),
        (date(year, 12, 25), "Juldagen", True),
        (date(year, 12, 26), "Annandag jul", True),
        # Named days that aren't red
        (date(year, 2, 14), "Alla hjärtans dag", False),
        (easter - timedelta(days=3), "Skärtorsdagen", False),
        (easter - timedelta(days=1), "Påskafton", False),
        (easter + timedelta(days=50), "Annandag pingst", False),
        (last_in_month(year, 5, SUN), "Mors dag", False),
        (midsummer - timedelta(days=1), "Midsommarafton", False),
        (date(year, 10, 31), "Halloween", False),
        (first_on_or_after(date(year, 11, 8), SUN), "Fars dag", False),
        (date(year, 12, 13), "Lucia", False),
        (date(year, 12, 24), "Julafton", False),
        (date(year, 12, 31), "Nyårsafton", False),
        # Lowercase, as they read after another name ("Påskdagen, sommartid börjar").
        # A day's text always starts with a capital letter.
        (last_in_month(year, 3, SUN), "sommartid börjar", False),
        (last_in_month(year, 10, SUN), "vintertid börjar", False),
    ]


HOLIDAY_CALENDARS = {
    "se": swedish_calendar,
    "none": lambda year: [],
}

# The first diary year the built-in calendar is right for. Until 2004 Annandag pingst was
# a red day and Nationaldagen wasn't, so Alfie refuses earlier years rather than guess.
FIRST_SWEDISH_YEAR = 2005

# ---------------------------------------------------------------------------
# Your dates and week notes: dates.md/.txt and weeknotes.md/.txt
# ---------------------------------------------------------------------------

# The order texts are listed in when a day has several:
# red days first, then your own notes, then the other built-in days.
RANK_RED, RANK_YOURS, RANK_BUILT_IN = 0, 1, 2

# A line may start with a Markdown list dash ("- 21 januari: ..."). A * first means red.
NOTE_LINE = re.compile(r"(?:[-+]\s+)?(\*)?\s*(\d{1,2})\.?\s+([^\W\d_]+)\.?\s*(?::(.*))?")
WEEKNOTE_LINE = re.compile(r"(?:[-+*]\s+)?(\d{1,2})\s*:(.*)")
OLD_FILE = re.compile(r"(holidays|notes|weeknotes)-\d{4}(-[a-z]{2})?\.txt|notes\.(txt|md)")
HEADING = re.compile(r"#+\s*(.*?)\s*#*")
EVERY_YEAR = {"every year", "varje år", "jedes jahr"}  # headings that end a year section


def _month_numbers():
    """Month names in all languages, and their first three letters, to month numbers."""
    numbers = {}
    for strings in LANGUAGES.values():
        for number, name in enumerate(strings["months"], start=1):
            numbers[name.casefold()] = number
            numbers.setdefault(name.casefold()[:3], number)
    return numbers


MONTH_NUMBERS = _month_numbers()


@dataclass
class DayInfo:
    """What goes on one day: whether it's red, and its texts."""
    red: bool = False
    entries: list = field(default_factory=list)  # (rank, order added, text)

    def add(self, text, red, rank):
        self.red = self.red or red
        if text:
            self.entries.append((rank, len(self.entries), text))

    @property
    def text(self):
        seen, texts = set(), []
        for _, _, text in sorted(self.entries):
            if text.casefold() not in seen:
                seen.add(text.casefold())
                texts.append(text)
        text = ", ".join(texts)
        return text[:1].upper() + text[1:]


@dataclass
class Notes:
    days: dict       # date -> DayInfo
    weeknotes: dict  # week number -> list of texts
    files: list      # the files that were read, for the summary


class NotesError(Exception):
    def __init__(self, problems):
        super().__init__("\n".join(problems))
        self.problems = problems


def plural(count, word):
    return f"{count} {word}{'' if count == 1 else 's'}"


def read_lines(path, problems):
    """(line number, text, year) for every line that isn't empty or a # comment. year comes
    from the nearest heading above that is a year ("## 2027"); None means every year.
    A heading "## Every year" (or "Varje år") goes back to every year."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        problems.append(f"{path.name}: please save it as UTF-8 text")
        return []
    lines, year = [], None
    for number, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if line.startswith("#"):
            title = HEADING.fullmatch(line).group(1)
            if re.fullmatch(r"\d{4}", title) and 1583 <= int(title) <= 9998:
                year = int(title)
            elif title.casefold() in EVERY_YEAR:
                year = None
        elif line:
            lines.append((number, line, year))
    return lines


def read_dates(path, problems):
    """[(year, month, day, text, red)] from a dates file. year is None for every year."""
    notes = []
    for number, line, year in read_lines(path, problems):
        where = f"{path.name}, line {number}"
        match = NOTE_LINE.fullmatch(line)
        if not match:
            problems.append(f"{where}: expected '<day> <month>: <text>', like '14 februari: Alla hjärtans dag'")
            continue
        star, day, month_name, text = match.groups()
        text = (text or "").strip()
        month = MONTH_NUMBERS.get(month_name.casefold())
        if month is None:
            problems.append(f"{where}: '{month_name}' isn't a month I know")
            continue
        try:
            date(year or 2000, month, int(day))  # 2000 was a leap year, so 29 februari is fine every year
        except ValueError:
            problems.append(f"{where}: there is no {int(day)} {month_name}" + (f" in {year}" if year else ""))
            continue
        if not text and not star:
            problems.append(f"{where}: nothing after the date (start the line with * to only make the day red)")
            continue
        notes.append((year, month, int(day), text, bool(star)))
    return notes


def read_weeknotes(path, problems):
    """[(year, week number, text)] from a week notes file. year is None for every year."""
    notes = []
    for number, line, year in read_lines(path, problems):
        where = f"{path.name}, line {number}"
        match = WEEKNOTE_LINE.fullmatch(line)
        if not match or not match.group(2).strip():
            problems.append(f"{where}: expected '<week number>: <text>'")
        elif not 1 <= int(match.group(1)) <= 53:
            problems.append(f"{where}: there is no week {int(match.group(1))}")
        else:
            notes.append((year, int(match.group(1)), match.group(2).strip()))
    return notes


def find_file(folder, names):
    """The first of names (dates.md, dates.txt) that's in the folder, or None."""
    found = [folder / name for name in names if (folder / name).exists()]
    if len(found) > 1:
        print(f"Note: both {found[0].name} and {found[1].name} are here. "
              f"I'm reading {found[0].name} and ignoring {found[1].name}.")
    return found[0] if found else None


def load_notes(year, holidays, folder, weeknotes=False):
    """Red days and notes for every date in the diary. The diary begins and ends with a few
    days of the neighbouring years, so those years are worked out too.
    Raises NotesError listing every line that can't be used."""
    problems, files, days = [], [], {}

    def add(day, text, red, rank):
        days.setdefault(day, DayInfo()).add(text, red, rank)

    notes = []
    path = find_file(folder, DATES_FILES)
    if path:
        notes = read_dates(path, problems)
        every = sum(1 for note in notes if note[0] is None)
        only = sum(1 for note in notes if note[0] == year)
        files.append(f"{path.name} ({every} every year, {only} for {year} only)")

    for this_year in (year - 1, year, year + 1):
        for day, name, red in HOLIDAY_CALENDARS[holidays](this_year):
            add(day, name, red, RANK_RED if red else RANK_BUILT_IN)
        for note_year, month, day, text, red in notes:
            if note_year not in (None, this_year):
                continue
            if (month, day) == (2, 29) and not calendar.isleap(this_year):
                day = 28  # an every-year note on 29 februari shows on 28 februari in other years
            add(date(this_year, month, day), text, red, RANK_RED if red else RANK_YOURS)

    week_texts = {}
    path = find_file(folder, WEEKNOTES_FILES) if weeknotes else None
    if path:
        used = [(week, text) for note_year, week, text in read_weeknotes(path, problems)
                if note_year in (None, year)]
        for week, text in used:
            week_texts.setdefault(week, []).append(text)
        files.append(f"{path.name} ({plural(len(used), 'week note')})")

    if problems:
        raise NotesError(problems)
    return Notes(days, week_texts, files)


def starter_dates(language, year):
    """A dates file to start from, with the format explained and examples commented out."""
    months = LANGUAGES[language]["months"]
    return f"""# Your own dates for Alfie's diary.
#
# One date per line:   <day> <month>: <text>
# Start a line with * to make the day red. Other lines starting with # are skipped.
# Holidays, Easter, Midsummer and so on are built in, so they don't go here.
#
# Dates at the top come back every year, like birthdays. Dates under a heading
# with a year, like the one below, are for that year only.
#
# Check what you'll get with:  {command_name()} list {year}
# Remove the # in front of an example to use it, or write your own.

# 14 {months[2]}: Example: a birthday

## {year}

# * 2 {months[0]}: Example: a day off, red
# 12 {months[5]}: Example: a trip
"""


def write_starter_dates(folder, language, year):
    existing = find_file(folder, DATES_FILES)
    if existing:
        print(f"There's already a {existing.name} here, so I've left it alone.", file=sys.stderr)
        return 1
    path = folder / "dates.txt"  # rename it dates.md to edit it as Markdown
    path.write_text(starter_dates(language, year), encoding="utf-8")
    print(f"Wrote {path.name}. Add your dates, then check them with: {command_name()} list {year}")
    return 0


def warn_about_old_files(folder):
    old = sorted(path.name for path in folder.iterdir() if OLD_FILE.fullmatch(path.name))
    if old:
        print(f"Note: {', '.join(old)} {'is' if len(old) == 1 else 'are'} no longer read.\n"
              f"      Holidays are built in now. Your own dates go in {' or '.join(DATES_FILES)}, "
              f"under a heading like '## 2027' if they're for one year only; see README.md.")

# ---------------------------------------------------------------------------
# LaTeX
# ---------------------------------------------------------------------------

LATEX_SPECIAL = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def latex_escape(text):
    """Make text safe for LaTeX, so an '&' or '%' in a note can't break the build."""
    return "".join(LATEX_SPECIAL.get(char, char) for char in text)


def separator(stretch=1, pagebreak=False):
    if pagebreak:
        return f"\\vspace{{\\stretch{{{stretch}}}}}\\pagebreak\n\n"
    return f"\\vspace{{\\stretch{{{stretch}}}}}\\rule{{\\textwidth}}{{0.1pt}}\\vspace{{-2mm}}\n\n"


def weekdots(filled):
    """Seven dots for the days of the week, the first `filled` of them black."""
    return "\\tikzcircle{2pt}{fill=black}\\hspace{2pt}" * filled + "\\tikzcircle{2pt}{}\\hspace{2pt}" * (7 - filled)


def week_number(day):
    return str(day.isocalendar()[1])


# For the column layouts. A page is one box, \AlfieAcross wide and \AlfieDown tall; on a turned
# page that's as wide as the page is tall, and \AlfieTurn turns it a quarter turn. On a week
# page the days stand in three columns with a line between each, reaching from just above the
# dates (\AlfieDayTop) down to the bottom margin. Where the dates go depends on the header, so
# the header is first set in a box on its own and measured. Minipages set \parskip to 0pt, so
# the page's \parskip is put back inside them, to space things as usual.
COLUMN_MACROS = r"""
\newlength\AlfieGap
\newlength\AlfieParskip
\AtBeginDocument{\setlength\AlfieParskip{\parskip}}
\newlength\AlfieDayTop \setlength\AlfieDayTop{3.4mm}
\newlength\AlfieColumnHeight
\newsavebox\AlfieHeaderBox
\newsavebox\AlfieDayBox
\newsavebox\AlfieNoteBox
\newcommand\AlfiePage[1]{\noindent\AlfieTurn{\begin{minipage}[b][\AlfieDown][t]{\AlfieAcross}%
  \setlength\parskip{\AlfieParskip}#1\end{minipage}}\newpage}
\newcommand\AlfieWeekPage[4]{%
  \sbox\AlfieHeaderBox{\begin{minipage}[b]{\AlfieAcross}\setlength\parskip{\AlfieParskip}%
    \rule{0pt}{\topskip}#1\par\normalsize\noindent\rule{0pt}{\AlfieDayTop}\end{minipage}}%
  \setlength\AlfieColumnHeight{\dimexpr\AlfieDown-\ht\AlfieHeaderBox+\AlfieDayTop\relax}%
  \AlfiePage{\rule{0pt}{\topskip}#1\par\normalsize\noindent
    \makebox[\linewidth][s]{\AlfieColumn{#2}\AlfieLine\AlfieColumn{#3}\AlfieLine\AlfieColumn{#4}}\par}}
\newcommand\AlfieColumn[1]{\begin{minipage}[t][\AlfieColumnHeight][s]{\dimexpr(\linewidth-4\AlfieGap)/3\relax}%
  \setlength\parskip{\AlfieParskip}\rule{0pt}{\AlfieDayTop}#1\vspace{\stretch{1}}\end{minipage}}
\newcommand\AlfieLine{\hfill\vrule width 0.1pt\hfill}
\newcommand\AlfieDay[2]{\sbox\AlfieDayBox{#1}\sbox\AlfieNoteBox{#2}%
  \ifdim\dimexpr\wd\AlfieDayBox+1em+\wd\AlfieNoteBox\relax>\linewidth
    \usebox\AlfieDayBox\par{\setlength\parskip{0pt}\raggedleft#2\par}%
  \else\usebox\AlfieDayBox\hfill\usebox\AlfieNoteBox\par\fi}
\newcommand\AlfieNoteUnder[1]{{\setlength\parskip{0pt}\raggedright#1\par}}
"""


class Diary:
    def __init__(self, year, paper, color, layout, language, notes):
        self.year = year
        self.paper = paper
        self.color = color
        self.layout = layout
        self.turned = layout in TURNED_LAYOUTS
        self.strings = LANGUAGES[language]
        self.notes = notes

    def latex(self, trimmed=False, back_offset=0.0):
        """The whole diary. trimmed: each PDF page is just the diary page, without the A4
        sheet and crop marks around it (for laying several on a sheet)."""
        layouts = {
            "w1p": self.week_on_one_page,
            "w1pnotes": self.week_with_notes_page,
            "w2p": lambda: self.week_on_two_pages(top_stretch=1, weekend_stretch=1),
            "w2pwf": lambda: self.week_on_two_pages(top_stretch=0.2, weekend_stretch=0.6),
            "1dp": self.day_per_page,
            "wg": self.week_gold,
            "w2pcolslandscape": self.week_in_columns,
            "w2pcolsportrait": self.week_in_columns,
        }
        return (self.preamble(trimmed, back_offset) + self.opening() + layouts[self.layout]()
                + "\\end{document}\n\n")

    # --- Days and weeks

    def weeks(self):
        """Monday-to-Sunday weeks covering the whole year."""
        first = date(self.year, 1, 1)
        monday = first - timedelta(days=first.weekday())
        weeks = []
        while monday <= date(self.year, 12, 31):
            weeks.append([monday + timedelta(days=i) for i in range(7)])
            monday += timedelta(days=7)
        return weeks

    def month_name(self, day):
        return self.strings["months"][day.month - 1]

    def day_name(self, day):
        return self.strings["days"][day.weekday()]

    def is_red(self, day):
        info = self.notes.days.get(day)
        return day.weekday() == SUN or bool(info and info.red)

    def note(self, day):
        info = self.notes.days.get(day)
        return info.text if info else ""

    def header(self, days):
        """'mars 2027', 'mars--april 2027' or 'december 2026--januari 2027' for the days on a page."""
        first, last = days[0], days[-1]
        if self.month_name(first) == self.month_name(last):
            return f"{self.month_name(first)} {first.year}"
        if first.year == last.year:
            return f"{self.month_name(first)}--{self.month_name(last)} {first.year}"
        return f"{self.month_name(first)} {first.year}--{self.month_name(last)} {last.year}"

    # --- Building blocks

    def preamble(self, trimmed=False, back_offset=0.0):
        paper = PAPERS[self.paper]
        # Turned, the page's top and bottom become its left and right edges, so they get the
        # outer margin, like the ends of the lines on an unturned page.
        top, bottom = (paper["margin"], paper["margin"]) if self.turned else (paper["top"], paper["bottom"])
        fill = "red!60!black" if self.color == "color" else "black"
        notes = "\\textcolor{red!60!black}{#1}" if self.color == "color" else "#1"
        lines = [
            "\\documentclass[11pt,titlepage]{article}",
            f"\\usepackage[{self.strings['babel']}]{{babel}}",
            "\\usepackage{fontspec}",
            "\\usepackage{graphicx}",
            "\\usepackage{parskip}",
            "\\usepackage{tikz}",
            "\\usepackage{pifont}",
            "\\usepackage[bookmarks=true,pdfborder={{0 0 0}}]{hyperref}",
            *(["\\usepackage[twoside]{geometry}"] if trimmed else [  # trimmed: the PDF page is the diary page
                "\\usepackage[dvips=false,pdftex=false,vtex=false,twoside]{geometry}",
                "\\usepackage[cross,a4,center,dvips,noinfo,odd]{crop}",  # one page per A4 sheet, crop marks
            ]),
            "\\defaultfontfeatures{Mapping=tex-text}",
            "\\setmainfont[BoldFont=Cronos Pro, ItalicFont=Cronos Pro Light Italic, "
            "BoldItalicFont=Cronos Pro Semibold, SlantedFont=Cronos Pro Bold, SmallCapsFont=Cronos Pro Light, "
            "SmallCapsFeatures={LetterSpace=1.15, Letters=SmallCaps}, Numbers={OldStyle, Proportional}, "
            "Scale=0.75] {Cronos Pro Light}",
            f"\\geometry{{paperwidth={paper['width']}mm, paperheight={paper['height']}mm, "
            f"margin={paper['margin']}mm, bottom={bottom}mm, top={top}mm, "
            f"left={paper['left']}mm, nohead}}",
            "",
            "\\newcommand*\\circled[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=1pt,"
            "minimum height=4.5mm,minimum width=4.5mm, line width=0.1pt] (char) {#1};}}",
            "",
            "\\newcommand*\\circledfill[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=0.1pt,"
            "minimum height=4.55mm,minimum width=4.55mm, line width=0.1pt, fill=" + fill + "] (char) {#1};}}",
            "\\newcommand*\\notescolor[1]{" + notes + "}",
            "",
            "\\newcommand{\\tikzcircle}[2]{\\tikz[baseline=-0.5ex]\\draw[#2,radius=#1,ultra thin] (0,0) circle ;}",
            "\\pagenumbering{gobble}",
            "",
        ]
        if self.turned:
            # The space between a column's text and the line beside it is the outer margin
            # too, which puts the lines between the days at a third and two thirds of the page.
            lines[-1:-1] = [*COLUMN_MACROS.strip().splitlines(),
                            "\\newcommand\\AlfieAcross{\\textheight}\\newcommand\\AlfieDown{\\textwidth}",
                            "\\newcommand\\AlfieTurn[1]{\\rotatebox{90}{#1}}",
                            f"\\setlength\\AlfieGap{{{paper['margin']}mm}}"]
        elif self.layout in COLUMN_LAYOUTS:
            # Upright, the columns are narrow: with 2 mm beside the lines, the longest weekday
            # (Donnerstag) and holiday word (Midsommardagen) still fit on pocket paper.
            lines[-1:-1] = [*COLUMN_MACROS.strip().splitlines(),
                            "\\newcommand\\AlfieAcross{\\textwidth}\\newcommand\\AlfieDown{\\textheight}",
                            "\\newcommand\\AlfieTurn[1]{#1}",
                            "\\setlength\\AlfieGap{2mm}"]
        if back_offset and not trimmed:
            # Every second page is the back of a sheet. Move it down by back_offset (page and
            # crop marks together) when it's written out, to make up for the printer.
            lines[-1:-1] = [
                "\\newcount\\AlfieSide\\newdimen\\AlfieFrontVoffset",
                "\\AddToHook{shipout/before}{\\global\\advance\\AlfieSide 1 "
                "\\ifnum\\AlfieSide=1 \\global\\AlfieFrontVoffset=\\voffset\\fi "
                "\\ifodd\\AlfieSide \\global\\voffset=\\AlfieFrontVoffset "
                f"\\else\\global\\voffset=\\dimexpr\\AlfieFrontVoffset+{back_offset:.2f}mm\\relax\\fi}}",
            ]
        return "\n".join(lines)

    def opening(self):
        s = self.strings
        title = (f"\\bfseries\\itshape \\Huge {s['the_year']} {self.year}\\\\ "
                 f"\\vspace{{0.25em}} \\Large \\normalfont {s['title'].format(paper=self.paper.title())}")
        author = f"\\emph{{{s['by']}}} {AUTHOR}"
        if self.turned:  # what \maketitle makes, on a turned page
            return (
                "\\begin{document}\n\n"
                "\\AlfiePage{\\centering\\vspace{\\stretch{1}}\n"
                f"{{\\LARGE {title}\\par}}\n\\vspace{{3em}}\n"
                f"{{\\large {author}\\par}}\n\\vspace{{1.5em}}\n"
                "{\\large \\today\\par}\n\\vspace{\\stretch{1}}}\n\n"
            )
        return (
            "\\begin{document}\n\n"
            f"\\title{{{title}}}\n"
            f"\\author{{{author}}}\n"
            "\\maketitle\n\n"
            "\\pagebreak\n\n"
        )

    def format_header(self, text, week, first_day=False, second_half=False):
        if second_half:
            header = f"\\hfill \\Large\\bfseries {text} \\normalfont\\normalsize\n\n"
        else:
            header = f"\\Large\\bfseries {text} \\hfill \\normalfont\\small {self.strings['week']} {week}\n\n"
        header += "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
        if first_day and not second_half:
            header += f"\\normalsize {self.strings['this_week']}\n\n"
        return header

    def day_heading(self, day):
        """(style, circle, weekday) for a day: the date in a circle and the weekday. Red days
        get a filled circle and italics, Saturdays a black circle."""
        number = str(day.day)
        style = "\\large\\bfseries "
        if self.is_red(day):  # before the Saturday check, so a red Saturday still looks red
            circle = "\\circledfill{\\bfseries\\textcolor{white}{" + number + "}} "
            style = "\\large\\bfseries\\itshape "
        elif day.weekday() == SAT:
            circle = ("\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=0.1pt,minimum height=4.55mm,"
                      "minimum width=4.55mm, line width=0.1pt, fill=black] (char) {\\bfseries\\textcolor{white}{"
                      + number + "}};}  ")
        else:
            circle = "\\circled{" + number + "} "
        return style, circle, "\\normalfont\\normalsize " + self.day_name(day)

    def format_day(self, day, recto):
        """The date in a circle, the weekday and any notes. On right-hand (recto) pages the
        date goes right."""
        note = latex_escape(self.note(day))
        style, circle, name = self.day_heading(day)
        if recto:
            text = "\\hfill " + name + " \\hspace{0mm} {" + style + circle.rstrip() + "}"  # in braces: the bold stays here
            if note:
                text = "\\small \\notescolor{" + note + "} " + text
        else:
            text = style + circle + " \\hspace{0mm} " + name
            if note:
                text += "\\hfill \\small \\notescolor{" + note + "}"
        return text + "\n\n"

    def column_day(self, day):
        """A day at the top of a column: the date and weekday as on a left-hand page. Turned,
        any notes go flush right beside them, or under them when there isn't room. Upright,
        the columns are narrow, so notes always go under, flush left: the whole width of the
        column is needed for a long word like Midsommardagen on pocket paper."""
        style, circle, name = self.day_heading(day)
        heading = style + circle + " \\hspace{0mm} " + name
        note = latex_escape(self.note(day))
        if not note:
            return heading + "\n\n"
        note = "{\\small \\notescolor{" + note + "}}"
        if self.turned:
            return "\\AlfieDay{" + heading + "}" + note + "\n\n"
        return heading + "\n\n\\AlfieNoteUnder" + note + "\n\n"

    # --- Layouts

    def week_on_one_page(self):  # w1p
        parts = []
        for page, week in enumerate(self.weeks()):
            parts.append(self.format_header(self.header(week), week_number(week[0])))
            for i, day in enumerate(week):
                parts.append(self.format_day(day, recto=page % 2 == 1))
                parts.append(separator(pagebreak=i == 6))
        return "".join(parts)

    def week_with_notes_page(self):  # w1pnotes: the week on the left, a notes page on the right
        parts = []
        for week in self.weeks():
            parts.append(self.format_header(self.header(week), week_number(week[0])))
            for i, day in enumerate(week):
                parts.append(self.format_day(day, recto=False))
                parts.append(separator(pagebreak=i == 6))
            parts.append(f"\\hfill \\small {self.strings['notes']} \n\n\\pagebreak\n\n")
        return "".join(parts)

    def week_on_two_pages(self, top_stretch, weekend_stretch):  # w2p and w2pwf
        parts = []
        for week in self.weeks():
            parts.append(self.format_header(self.header(week[0:3]), week_number(week[0]), first_day=True))
            parts.append(separator(stretch=top_stretch))
            for i in range(3):  # Monday to Wednesday on the left
                parts.append(self.format_day(week[i], recto=False))
                parts.append(separator(pagebreak=i == 2))
            parts.append(self.format_header(self.header(week[3:7]), "", second_half=True))
            for i in range(3, 7):  # Thursday to Sunday on the right
                parts.append(self.format_day(week[i], recto=True))
                parts.append(separator(stretch=weekend_stretch if i >= 5 else 1, pagebreak=i == 6))
        return "".join(parts)

    def day_per_page(self):  # 1dp
        parts = []
        days = [day for week in self.weeks() for day in week]
        for page, day in enumerate(days):  # the first day is on a left-hand page
            parts.append(self.format_header(f"{self.month_name(day)} {day.year}", week_number(day)))
            parts.append(self.format_day(day, recto=page % 2 == 1))
            parts.append(separator(pagebreak=True))
        return "".join(parts)

    def week_gold(self):  # wg: four pages a week
        parts = []
        for week in self.weeks():
            number = week_number(week[0])
            mon, tue, wed, thu, fri, sat, sun = week

            # Left: Monday to Wednesday
            parts.append(self.format_header(self.header(week[0:3]), number, first_day=True))
            parts.append(self.format_day(mon, recto=False))
            for day in (tue, wed):
                parts.append(separator())
                parts.append(self.format_day(day, recto=False))
            parts.append("\\vspace{\\stretch{1}}\n" + weekdots(3) + "\\pagebreak\n\n")

            # Right: Thursday and Friday
            parts.append(self.format_header(self.header(week[3:5]), "", second_half=True))
            parts.append(self.format_day(thu, recto=True))
            parts.append(separator())
            parts.append(self.format_day(fri, recto=True))
            parts.append("\\footnotesize \\ding{93} \n\n\\vspace{\\stretch{1}}\n\\hfill" + weekdots(5)
                         + "\\pagebreak\n\n")

            # Left: the weekend
            parts.append(self.format_header(self.header(week[5:7]), number))
            parts.append(self.format_day(sat, recto=False))
            parts.append(separator())
            parts.append(self.format_day(sun, recto=False))
            parts.append("\\hfill \\footnotesize \\ding{93} \n\n\\vspace{\\stretch{1}}\n" + weekdots(7)
                         + "\\pagebreak\n\n")

            # Right: week note and gratitude
            parts.append("\\hfill \\Large\\bfseries " + self.header(week[5:7]) + " \\normalfont\\normalsize\n\n")
            parts.append("\\vspace{-4.5mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n")
            texts = self.notes.weeknotes.get(int(number), [])
            if texts:
                parts.append("\n\n".join(latex_escape(text) for text in texts) + "\n\n")
            parts.append("\\vspace{\\stretch{3}}\\rule{2cm}{0.1pt}\n\n")
            parts.append("\\vspace{-2mm}" + self.strings["gratitude"] + "\n\n")
            parts.append("\\vspace{\\stretch{1}}\n\n\\pagebreak\n\n")
        return "".join(parts)

    def week_in_columns(self):  # w2pcolslandscape and w2pcolsportrait
        parts = []
        for week in self.weeks():
            number = week_number(week[0])
            mon, tue, wed, thu, fri, sat, sun = week
            weekend = self.column_day(sat) + separator() + self.column_day(sun)  # sharing a column
            pages = [(week[0:3], [self.column_day(mon), self.column_day(tue), self.column_day(wed)]),
                     (week[3:7], [self.column_day(thu), self.column_day(fri), weekend])]
            for days, columns in pages:  # left-hand page (above the rings when turned), then right
                header = self.format_header(self.header(days), number)
                parts.append("\\AlfieWeekPage{" + header + "}{" + "}{".join(columns) + "}\n\n")
        return "".join(parts)

    # --- Checking

    def print_list(self):
        print(f"\nRed days (●) and notes for {self.year}. Ordinary Sundays are red too, but aren't marked.\n")
        for day in sorted(day for day in self.notes.days if day.year == self.year):
            info = self.notes.days[day]
            if info.text or info.red:
                mark = "●" if info.red else " "
                print(f"{day.day:>3} {self.month_name(day)[:3]} {self.day_name(day)[:3]}  {mark} {info.text}")

# ---------------------------------------------------------------------------
# Saving paper: several diary pages on each A4 sheet, printed two-sided
# ---------------------------------------------------------------------------

SHEET_WIDTH, SHEET_HEIGHT = 210.0, 297.0  # A4, portrait, mm
SHEET_MARGIN = 10.0                       # at least this much paper around the pages
SHEET_GUTTER = 10.0                       # paper between pages, room for crop marks
CROSS_ARM = 20.0                          # crop marks: a cross on each page corner, this long each way
PILES = "ABCDEFGH"


@dataclass
class SheetLayout:
    cols: int
    rows: int
    turned: bool   # pages turned a quarter turn, because more of them fit that way
    width: float   # a page's size on the sheet, after turning, mm
    height: float

    @property
    def per_side(self):
        return self.cols * self.rows


@dataclass
class Placement:
    slot: int      # where on the sheet: 0 is pile A (top left), then reading order
    page: int      # diary page, from 1
    box: tuple     # (left, bottom, right, top) on the sheet, mm from its lower left corner
    angle: int     # turned this many degrees counterclockwise


def sheet_layout(paper):
    """The arrangement that fits the most pages of this size on an A4 sheet, or None if only
    one fits. Sheets stay portrait, so the usual two-sided setting (flip on the long edge)
    is the right one; pages are turned instead when that fits more of them."""
    width, height = float(PAPERS[paper]["width"]), float(PAPERS[paper]["height"])
    best = None
    for turned in (False, True):
        w, h = (height, width) if turned else (width, height)
        cols = int((SHEET_WIDTH - 2 * SHEET_MARGIN + SHEET_GUTTER) // (w + SHEET_GUTTER))
        rows = int((SHEET_HEIGHT - 2 * SHEET_MARGIN + SHEET_GUTTER) // (h + SHEET_GUTTER))
        if cols * rows > (best.per_side if best else 1):
            best = SheetLayout(cols, rows, turned, w, h)
    return best


def sheet_count(layout, page_count):
    leaves = (page_count + 1) // 2
    return -(-leaves // layout.per_side)  # rounded up


def block_box(layout):
    """(left, bottom, right, top) of all the pages on a sheet together, centred on it."""
    width = layout.cols * layout.width + (layout.cols - 1) * SHEET_GUTTER
    height = layout.rows * layout.height + (layout.rows - 1) * SHEET_GUTTER
    left, bottom = (SHEET_WIDTH - width) / 2, (SHEET_HEIGHT - height) / 2
    return left, bottom, left + width, bottom + height


def sheet_plan(layout, page_count, back_offset=0.0):
    """Where every diary page goes: a list of sheet sides (front, back, front, back, ...),
    each a list of Placements.

    Each leaf of the diary has two pages: page 2n+1 on its front and 2n+2 on its back.
    The leaves are spread for cut-and-stack: slot k of sheet s holds leaf k*sheets + s.
    So when the whole pile is cut along the crop marks, the piles stacked A on top of B
    (on top of C ...) give the leaves in order, without any sorting.

    The sheets are printed two-sided and flipped on their long edge, so the back of a slot
    is at the same height but mirrored left to right. Pages turned clockwise on the front
    are turned counterclockwise on the back, so both tops end up at the same edge of the leaf.
    back_offset (mm) moves everything on the back down, for a printer that prints it higher."""
    sheets = sheet_count(layout, page_count)
    first_left, _, _, first_top = block_box(layout)
    sides = []
    for sheet in range(sheets):
        front, back = [], []
        for slot in range(layout.per_side):
            leaf = slot * sheets + sheet
            left = first_left + (slot % layout.cols) * (layout.width + SHEET_GUTTER)
            top = first_top - (slot // layout.cols) * (layout.height + SHEET_GUTTER)
            box = (left, top - layout.height, left + layout.width, top)
            behind = (SHEET_WIDTH - box[2], box[1] - back_offset, SHEET_WIDTH - box[0], box[3] - back_offset)
            if 2 * leaf + 1 <= page_count:
                front.append(Placement(slot, 2 * leaf + 1, box, -90 if layout.turned else 0))
            if 2 * leaf + 2 <= page_count:
                back.append(Placement(slot, 2 * leaf + 2, behind, 90 if layout.turned else 0))
        sides += [front, back]
    return sides


def mm(value):
    return f"{value:.2f}"


def cross_lines(box):
    """The crop marks for a page: a cross centred on each corner, its arms running along the
    page's edges both outwards and inwards (like the crop package's cross marks in the one page
    per sheet version). Each arm lies on a cutting line, so cutting removes it, and a piece of
    the sheet keeps the marks for every edge that is still to be cut.
    Returns line segments as ((x1, y1), (x2, y2))."""
    left, bottom, right, top = box
    lines = []
    for x in (left, right):
        for y in (bottom, top):
            lines.append(((x - CROSS_ARM, y), (x + CROSS_ARM, y)))
            lines.append(((x, y - CROSS_ARM), (x, y + CROSS_ARM)))
    return lines


def crop_marks(box):
    marks = []
    for (x1, y1), (x2, y2) in cross_lines(box):
        if y1 == y2:
            marks.append(f"\\put({mm(x1)},{mm(y1)}){{\\line(1,0){{{mm(x2 - x1)}}}}}")
        else:
            marks.append(f"\\put({mm(x1)},{mm(y1)}){{\\line(0,1){{{mm(y2 - y1)}}}}}")
    return "".join(marks)


def label_span(layout):
    """(left, right) of the widest stretch of the top and bottom margins that no cross reaches
    into, for the sheet number and the printing instructions."""
    first_left = block_box(layout)[0]
    edges = [SHEET_MARGIN, SHEET_WIDTH - SHEET_MARGIN]
    for col in range(layout.cols):
        left = first_left + col * (layout.width + SHEET_GUTTER)
        edges += [left, left + layout.width]
    edges.sort()
    return max(zip(edges, edges[1:]), key=lambda span: span[1] - span[0])


def sheets_latex(layout, page_count, pages_pdf, title, back_offset=0.0):
    """A4 sheets with the pages of pages_pdf (one diary page per PDF page) laid out by
    sheet_plan, with crop marks and pile letters on the fronts."""
    sides = sheet_plan(layout, page_count, back_offset)
    piles = PILES[:layout.per_side]
    block = block_box(layout)
    below, above = block[1] / 2, (block[3] + SHEET_HEIGHT) / 2  # middle of the bottom and top margins
    span_left, span_right = label_span(layout)
    label_x, label_width = (span_left + span_right) / 2, span_right - span_left - 6

    def label(y, text):
        return (f"\\put({mm(label_x)},{mm(y)}){{\\makebox(0,0){{\\parbox{{{mm(label_width)}mm}}"
                f"{{\\centering\\scriptsize {text}}}}}}}")
    lines = [
        "\\documentclass{article}",
        "\\usepackage[a4paper,margin=0mm]{geometry}",
        "\\usepackage{graphicx}",
        "\\usepackage{eso-pic}",
        "\\pagestyle{empty}",
        "\\begin{document}",
        "\\sffamily",
    ]
    for number, side in enumerate(sides):
        front = number % 2 == 0
        items = ["\\setlength{\\unitlength}{1mm}\\linethickness{0.4pt}"]
        for place in side:
            left, bottom, right, top = place.box
            middle = (bottom + top) / 2
            items.append(f"\\put({mm((left + right) / 2)},{mm(middle)}){{\\makebox(0,0){{"
                         f"\\includegraphics[page={place.page},angle={place.angle}]{{{pages_pdf}}}}}}}")
            if front:
                items.append(crop_marks(place.box))
                on_right = layout.cols > 1 and place.slot % layout.cols == layout.cols - 1
                x = right + 9 if on_right else left - 9
                items.append(f"\\put({mm(x)},{mm(middle)}){{\\makebox(0,0){{\\small {piles[place.slot]}}}}}")
        if front:
            items.append(label(below, f"{title}: sheet {number // 2 + 1} of {len(sides) // 2}"))
        if number == 0:
            items.append(label(above, "Print two-sided, flipping on the long edge, at 100\\,\\% size. "
                                      f"Cut along the crop marks, then stack the piles with A on top: "
                                      f"{', '.join(piles)}."))
        lines.append("\\AddToShipoutPictureBG*{\\AtPageLowerLeft{" + "".join(items) + "}}")
        lines.append("\\null\\newpage")
    lines.append("\\end{document}")
    return "\n".join(lines) + "\n"


def printing_instructions(layout, page_count):
    piles = PILES[:layout.per_side]
    return (f"{sheet_count(layout, page_count)} sheets, {layout.per_side} pages on each side.\n"
            "Print them two-sided, flipping on the long edge (the usual setting), at 100 % size.\n"
            f"Cut the whole pile along the crop marks, then stack the piles {', '.join(piles)} with A on top.")

# ---------------------------------------------------------------------------
# Typesetting
# ---------------------------------------------------------------------------

MACTEX_XELATEX = "/Library/TeX/texbin/xelatex"


def latex_error(log, output):
    """The first error in XeLaTeX's log, with the lines that say where it is."""
    try:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        lines = output.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("!"):
            excerpt = lines[i:i + 12]
            for j, text in enumerate(excerpt):
                if text.startswith("l."):  # "l.123 ..." is where in the .tex file it went wrong
                    return "\n".join(excerpt[:j + 2]).rstrip()
            return "\n".join(excerpt[:6])
    return "\n".join(lines[-15:])


def run_xelatex(tex):
    """Typeset a .tex file where it is. Returns the number of pages, or None after showing
    what went wrong."""
    xelatex = shutil.which("xelatex") or (MACTEX_XELATEX if os.path.exists(MACTEX_XELATEX) else None)
    if not xelatex:
        print("I can't find XeLaTeX. Install MacTeX, or add the word tex-only to just write the LaTeX file.",
              file=sys.stderr)
        return None
    built, log = tex.with_suffix(".pdf"), tex.with_suffix(".log")
    built.unlink(missing_ok=True)
    result = subprocess.run(
        [xelatex, "-interaction=nonstopmode", "-halt-on-error", tex.name],
        cwd=tex.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace",
    )
    if result.returncode != 0 or not built.exists():
        print("\nXeLaTeX stopped with an error:\n", file=sys.stderr)
        print(latex_error(log, result.stdout), file=sys.stderr)
        print(f"\nThe whole log is in {log}", file=sys.stderr)
        return None
    try:
        text = log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = result.stdout
    # The log wraps long lines, so join them before looking for "Output written on x.pdf (107 pages".
    match = re.search(r"Output written on .*?\((\d+) pages?", text.replace("\n", ""))
    return int(match.group(1)) if match else 0


def typeset(tex, out_folder):
    """Typeset a .tex file and move the PDF to out_folder. Returns the PDF, or None."""
    if run_xelatex(tex) is None:
        return None
    pdf = out_folder / tex.with_suffix(".pdf").name
    os.replace(tex.with_suffix(".pdf"), pdf)
    return pdf


def remove_build_files(build, name, keep):
    """After a successful run, delete this diary's LaTeX files (.tex, .aux, .log, .out and
    in-between PDFs) from build/, and build/ itself if that empties it. After a failed run
    they stay, so the log can be read."""
    for path in build.glob(f"{name}*"):
        if path.is_file() and path.resolve() != keep.resolve():
            path.unlink()
    if build.resolve() != keep.parent.resolve():
        try:
            build.rmdir()
        except OSError:
            pass  # other files are still in there

# ---------------------------------------------------------------------------
# Words: what you type, after alfie or in Alfie's shell
# ---------------------------------------------------------------------------

VERSION = "3.0"
FOLDER = Path(__file__).resolve().parent  # Alfie's files live next to alfie.py, wherever you run it from

# Where "alfie install" puts the alfie command: the first of these that is on PATH and writable.
INSTALL_DIRS = [Path.home() / ".local" / "bin", Path.home() / "bin", Path("/opt/homebrew/bin"), Path("/usr/local/bin")]


def next_year():
    return date.today().year + 1


@dataclass
class Settings:
    year: int = field(default_factory=next_year)
    paper: str = DEFAULTS["paper"]
    layout: str = DEFAULTS["layout"]
    language: str = DEFAULTS["language"]
    color: str = DEFAULTS["color"]
    save_paper: bool = DEFAULTS["save_paper"]
    holidays: str = ""  # "se" or "none"; "" means the Swedish calendar for Swedish diaries
    tex_only: bool = False
    open_pdf: bool = True
    back_offset: float = DEFAULTS["back_offset"]  # mm, + moves the back of each sheet down

    @property
    def calendar(self):
        return self.holidays or ("se" if self.language == "sv" else "none")

    def describe(self):
        """The settings on one line, as the shell shows them."""
        parts = [str(self.year), self.paper, self.layout, self.language, self.color]
        if self.save_paper:
            sheet = sheet_layout(self.paper)
            parts.append(f"{sheet.per_side} pages per sheet" if sheet else f"save-paper (doesn't fit {self.paper})")
        if self.back_offset:
            parts.append(f"back {signed_mm(self.back_offset)} mm")
        if self.calendar == "none":
            parts.append("no holidays")
        if self.tex_only:
            parts.append("tex-only")
        if not self.open_pdf:
            parts.append("no-open")
        return " · ".join(parts)

    def words(self):
        """The words that give these settings, leaving out the usual ones."""
        usual = Settings()
        words = [str(self.year)]
        words += [getattr(self, name) for name in ("paper", "layout", "language", "color")
                  if getattr(self, name) != getattr(usual, name)]
        if self.save_paper != usual.save_paper:
            words.append("save-paper" if self.save_paper else "no-save-paper")
        if self.back_offset != usual.back_offset:
            words.append(f"back={signed_mm(self.back_offset)}")
        if self.holidays:
            words.append("holidays" if self.holidays == "se" else "no-holidays")
        if self.tex_only:
            words.append("tex-only")
        if not self.open_pdf:
            words.append("no-open")
        return words


LANGUAGE_NAMES = {"sv": "Swedish", "de": "German", "en": "English"}
BACK_WORD = re.compile(r"back=?([+-]?\d+(?:[.,]\d+)?)")  # back=+1.0, back=-0.5, back+0,9 ...
MAX_BACK_OFFSET = 10.0  # mm


def signed_mm(value):
    """+1.0, -0.5, +0.95 or 0."""
    if not value:
        return "0"
    text = f"{value:+.2f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


def back_meaning(value):
    if not value:
        return "the back of each sheet isn't moved"
    return f"the back of each sheet moved {abs(value):g} mm {'down' if value > 0 else 'up'}"


def setting_rows(s):
    """[(label, value, what it means)] for every setting."""
    size = PAPERS[s.paper]
    sheet = sheet_layout(s.paper)
    if not s.save_paper:
        saving = "one page per A4 sheet"
    elif sheet:
        saving = f"{sheet.per_side} pages on each A4 sheet"
    else:
        saving = f"but only one {s.paper} page fits on an A4 sheet"
    year = {next_year(): "next year", date.today().year: "this year"}.get(s.year, "")
    return [
        ("Year", str(s.year), year),
        ("Paper", s.paper, f"{size['width']} × {size['height']} mm"),
        ("Layout", s.layout, LAYOUTS[s.layout]),
        ("Language", s.language, LANGUAGE_NAMES[s.language]),
        ("Colour", s.color, "red days and notes in red" if s.color == "color" else "black and white"),
        ("Save paper", "on" if s.save_paper else "off", saving),
        ("Back side", f"{signed_mm(s.back_offset)} mm", back_meaning(s.back_offset)),
        ("Holidays", "on" if s.calendar == "se" else "off",
         "the Swedish calendar" if s.calendar == "se" else "only Sundays are red"),
        ("Output", "tex-only" if s.tex_only else "pdf", "only the LaTeX file" if s.tex_only else "a typeset PDF"),
        ("Open PDF", "yes" if s.open_pdf else "no", "when it's done" if s.open_pdf else "leave it closed"),
    ]


def settings_table(settings, before=None):
    """The settings, one per line, with what each one means. With before, only the lines that
    changed. Output and Open PDF are left out while they're the usual pdf and yes."""
    rows = setting_rows(settings)
    if before is None:
        rows = rows[:8] + [row for row in rows[8:] if row[1] not in ("pdf", "yes")]
    else:
        rows = [row for row, old in zip(rows, setting_rows(before)) if row != old]
    width = max([10] + [len(value) + 2 for _, value, _ in rows])  # wider for a long layout name
    return "\n".join(f"  {label:<11}{value:<{width}}{meaning}".rstrip() for label, value, meaning in rows)


COMMANDS = ["make", "list", "settings", "init", "install", "help", "quit"]
COMMAND_ALIASES = {"h": "help", "?": "help", "exit": "quit", "q": "quit", "show": "settings"}

SETTING_WORDS = {
    **{paper: ("paper", paper) for paper in PAPERS},
    **{layout: ("layout", layout) for layout in LAYOUTS},
    **{language: ("language", language) for language in LANGUAGES},
    "color": ("color", "color"), "colour": ("color", "color"), "bw": ("color", "bw"),
    "save-paper": ("save_paper", True), "no-save-paper": ("save_paper", False),
    "holidays": ("holidays", "se"), "se": ("holidays", "se"),
    "no-holidays": ("holidays", "none"), "none": ("holidays", "none"),
    "tex-only": ("tex_only", True), "pdf": ("tex_only", False),
    "no-open": ("open_pdf", False), "open": ("open_pdf", True),
}

# A setting's name on its own shows its choices. Before a value it's simply skipped, so the
# old way of writing options ("--paper pocket --save-paper") still works.
CHOICES = {
    "paper": "Paper sizes: " + ", ".join(f"{name} ({size['width']} × {size['height']} mm)"
                                        for name, size in PAPERS.items()),
    "layout": "Layouts:\n" + "\n".join(f"  {name:<{max(map(len, LAYOUTS))}} {text}" for name, text in LAYOUTS.items()),
    "lang": "Languages: sv (Swedish), de (German), en (English)",
    "year": "The year: four digits, like 2028. Without one you get next year's diary.",
    "back": "Back side: back=+1.0 moves the back of each sheet 1.0 mm down, for a printer that "
            "prints the back higher than the front; back=-0.5 moves it up, back=0 not at all.",
}
CHOICES["language"] = CHOICES["lang"]

ALL_WORDS = sorted(set(COMMANDS) | set(COMMAND_ALIASES) | set(SETTING_WORDS) | set(CHOICES))


class WordError(Exception):
    pass


def command_name():
    """How to run Alfie from a terminal: alfie once it's installed, otherwise ./alfie.py."""
    found = shutil.which("alfie")
    return "alfie" if found and Path(found).resolve() == Path(__file__).resolve() else "./alfie.py"


def unknown_word(given):
    word = given.lower().strip("-")
    parts = word.split("-")
    if len(parts) > 2 and all(part in SETTING_WORDS or part in COMMANDS or part in ("yes", "no")
                              or (part.isdigit() and len(part) == 4) for part in parts):
        words = " ".join(part for part in parts if part not in ("yes", "no"))
        return f"Put spaces between the words, not dashes: {command_name()} {words}"
    close = difflib.get_close_matches(word, ALL_WORDS, n=1, cutoff=0.6)
    hint = f"Did you mean {close[0]}?" if close else f"{command_name()} help shows them all."
    return f"I don't know the word '{given}'. {hint}"


def parse_words(words, settings):
    """Apply words, in any order, to a copy of settings. Returns (the command or None, the
    new settings, the setting names given on their own). A word Alfie doesn't know raises
    WordError, with a suggestion, and nothing changes."""
    new = replace(settings)
    command, named = None, []
    for given in words:
        word = given.lower().lstrip("-")
        if not word:
            continue
        if word.isdigit():
            if len(word) != 4 or not 1583 <= int(word) <= 9998:
                raise WordError(f"'{given}' isn't a year I can make: four digits, like {next_year()}.")
            new.year = int(word)
        elif word in COMMANDS or word in COMMAND_ALIASES:
            name = COMMAND_ALIASES.get(word, word)
            if command and command != name:
                raise WordError(f"One command at a time, please: {command} or {name}.")
            command = name
        elif word in SETTING_WORDS:
            setattr(new, *SETTING_WORDS[word])
        elif BACK_WORD.fullmatch(word):
            offset = float(BACK_WORD.fullmatch(word).group(1).replace(",", "."))
            if abs(offset) > MAX_BACK_OFFSET:
                raise WordError(f"'{given}' moves the back side more than {MAX_BACK_OFFSET:g} mm; "
                                "a printer is usually off by a millimetre or two.")
            new.back_offset = offset
        elif word in CHOICES:
            named.append(word)
        else:
            raise WordError(unknown_word(given))
    return command, new, named


def help_text():
    me, usual = command_name(), Settings()
    return f"""Alfie {VERSION} makes diary inserts. Give it words, in any order:

  {me} 2027                     the 2027 diary, with your usual settings
  {me} 2027 pocket save-paper   pocket size, four pages on each A4 sheet
  {me} list 2027                the red days and notes it will show
  {me}                          a shell, where you type the same words

Commands     make (the default), list, settings, init, install, help
Year         four digits; without one, next year ({usual.year})
Paper        {", ".join(PAPERS)}  (paper on its own shows the sizes)
Layout       {", ".join(LAYOUTS)}  (layout on its own says what they are)
Language     {", ".join(LANGUAGES)}
Colour       color, bw
Save paper   save-paper, no-save-paper  (pocket: 4 pages per A4 sheet, personal and a6: 2)
Back side    back=+1.0 moves the back of each sheet 1 mm down, back=-0.5 up (now {signed_mm(usual.back_offset)})
Holidays     holidays, no-holidays  (the built-in Swedish calendar)
Output       tex-only, pdf, no-open, open

Your usual settings: {usual.describe()}  (DEFAULTS at the top of alfie.py)
Your dates go in dates.md or dates.txt in {FOLDER}. More in README.md."""


def install(candidates=None):
    """Make the alfie command work in any terminal folder, with a link to this file in a
    folder on PATH."""
    me = Path(__file__).resolve()
    on_path = {Path(entry).expanduser() for entry in os.environ.get("PATH", "").split(os.pathsep) if entry}
    for folder in candidates or INSTALL_DIRS:
        if folder not in on_path or not folder.is_dir() or not os.access(folder, os.W_OK):
            continue
        link = folder / "alfie"
        if link.is_symlink() and link.resolve() == me:
            print(f"The alfie command is already installed: {link} → {me}")
            return 0
        if link.exists() or link.is_symlink():
            print(f"There's already something called {link}, so I've left it alone.", file=sys.stderr)
            return 1
        link.symlink_to(me)
        print(f"Installed {link} → {me}\nNow alfie works in any terminal folder. To undo it: rm {link}")
        return 0
    print("I can't find a folder on your PATH to put the alfie command in. One way to make one:\n"
          f"  mkdir -p ~/.local/bin && ln -s '{me}' ~/.local/bin/alfie\n"
          "then add this line to ~/.zshrc:  export PATH=\"$HOME/.local/bin:$PATH\"", file=sys.stderr)
    return 1


def make_diary(settings, folder, list_only=False):
    """Make the diary, or with list_only show its red days and notes. Returns an exit status."""
    s = settings
    if s.calendar == "se" and s.year < FIRST_SWEDISH_YEAR:
        print(f"The built-in Swedish calendar follows the holiday law as it has been since {FIRST_SWEDISH_YEAR}; "
              f"{s.year} had other red days.\nAdd the word no-holidays, and mark that year's red days with * "
              "in your dates file.", file=sys.stderr)
        return 1
    warn_about_old_files(folder)
    try:
        notes = load_notes(s.year, s.calendar, folder, weeknotes=s.layout == "wg")
    except NotesError as error:
        print("Please fix these lines first:\n" + "\n".join(f"  {problem}" for problem in error.problems),
              file=sys.stderr)
        return 1

    calendar_text = "the Swedish calendar" if s.calendar == "se" else "no built-in calendar (only Sundays are red)"
    files_text = ", ".join(notes.files) if notes.files else f"no dates file yet ({command_name()} init makes one)"
    using = f"Using {calendar_text} and {files_text}."
    diary = Diary(s.year, s.paper, s.color, s.layout, s.language, notes)
    if list_only:
        print(using)
        diary.print_list()
        return 0

    sheet = sheet_layout(s.paper) if s.save_paper else None
    if s.save_paper and sheet is None:
        print(f"Only one {s.paper} page fits on an A4 sheet, so it's one page per sheet as usual.")
    if sheet and s.tex_only:
        print("Saving paper needs the typeset pages, so tex-only gives the usual one page per sheet.")
        sheet = None

    per_sheet = f", {sheet.per_side} pages per A4 sheet" if sheet else ""
    colour = "colour" if s.color == "color" else "black and white"
    back = f", back side {signed_mm(s.back_offset)} mm" if s.back_offset else ""
    print(f"Making the {s.year} diary: {s.paper}, {s.layout}, {LANGUAGE_NAMES[s.language]}, {colour}{per_sheet}{back}.")
    print(using)
    build = folder / BUILD_DIR
    build.mkdir(exist_ok=True)
    name = f"diary-{s.paper}-{s.year}-{s.language}"
    tex = build / (f"{name}-pages.tex" if sheet else f"{name}.tex")
    tex.write_text(diary.latex(trimmed=bool(sheet), back_offset=s.back_offset), encoding="utf-8")
    if s.tex_only:
        print(f"Wrote {tex.relative_to(folder)} (tex-only, so it isn't typeset).")
        return 0

    print("Typesetting with XeLaTeX ...")
    if sheet:
        page_count = run_xelatex(tex)
        if page_count is None:
            return 1
        sheets_tex = build / f"{name}-{sheet.per_side}up.tex"
        sheets_tex.write_text(sheets_latex(sheet, page_count, tex.with_suffix(".pdf").name,
                                           f"Alfie {s.year}, {s.paper}", s.back_offset), encoding="utf-8")
        tex = sheets_tex
    pdf = typeset(tex, folder)
    if pdf is None:
        return 1
    remove_build_files(build, name, keep=pdf)
    print(f"Done: {pdf.name}")
    if sheet:
        print(printing_instructions(sheet, page_count))
    if s.open_pdf and sys.platform == "darwin":
        subprocess.run(["open", str(pdf)], check=False)
    return 0


def run_command(command, settings, folder):
    if command == "help":
        print(help_text())
        return 0
    if command == "settings":
        print(settings_table(settings))
        return 0
    if command == "install":
        return install()
    if command == "init":
        return write_starter_dates(folder, settings.language, settings.year)
    return make_diary(settings, folder, list_only=command == "list")

# ---------------------------------------------------------------------------
# The shell: alfie on its own
# ---------------------------------------------------------------------------


def setup_completion():
    """Tab completes Alfie's words in the shell."""
    try:
        import readline
    except ImportError:
        return

    def complete(text, state):
        matches = [word for word in ALL_WORDS + ["back="] if word.startswith(text.lower())]
        return matches[state] if state < len(matches) else None

    readline.set_completer(complete)
    readline.set_completer_delims(" \t")
    if "libedit" in (readline.__doc__ or ""):  # the readline that comes with macOS
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")


SHELL_INTRO = """
Change a setting by typing its new value, like 2028, pocket, wg, color or save-paper.
Then type make to make the diary, or list to see its red days and notes.
help shows all the words, and quit leaves."""


def shell_help(settings):
    """Every word, for the shell: the commands, and each setting's choices with the current
    one marked."""
    s = settings

    def choices(values, current):
        return "  ".join(f"{value}*" if value == current else value for value in values)

    return "\n".join([
        "Commands",
        "  make        make the diary",
        "  list        show the red days and notes",
        "  settings    show all the settings",
        "  init        write a starter dates file, if you don't have one",
        "  install     make the alfie command work in any terminal folder",
        "  help        this list",
        "  quit        leave (Ctrl-D works too)",
        "",
        "Settings: type a new value to change one. * marks the current value.",
        f"  Year        four digits, like {next_year()}",
        f"  Paper       {choices(PAPERS, s.paper)}",
        f"  Layout      {choices(LAYOUTS, s.layout)}    (layout on its own says what they are)",
        f"  Language    {choices(LANGUAGES, s.language)}",
        f"  Colour      {choices(['color', 'bw'], s.color)}",
        f"  Save paper  {choices(['save-paper', 'no-save-paper'], 'save-paper' if s.save_paper else 'no-save-paper')}",
        f"  Back side   back=+1.0, back=0, back=-0.5 and so on: mm, + moves the back of each sheet down "
        f"(now {signed_mm(s.back_offset)})",
        f"  Holidays    {choices(['holidays', 'no-holidays'], 'holidays' if s.calendar == 'se' else 'no-holidays')}",
        f"  Output      {choices(['pdf', 'tex-only'], 'tex-only' if s.tex_only else 'pdf')}",
        f"  Open PDF    {choices(['open', 'no-open'], 'open' if s.open_pdf else 'no-open')}",
        "",
        "Several words at once work too, like: 2028 pocket save-paper make",
    ])


def shell(folder, settings=None):
    """Read lines of words until quit. Settings stay from one line to the next."""
    settings = settings or Settings()
    if sys.stdin.isatty():
        setup_completion()
    print(f"Alfie {VERSION} makes diary inserts. The settings are:\n")
    print(settings_table(settings))
    print(SHELL_INTRO)
    told_shortcut = False
    while True:
        try:
            line = input("\nalfie> ")
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print("\n(Type quit to leave.)")
            continue
        words = line.split()
        if words and (words[0].lower() == "alfie" or words[0].endswith("alfie.py")):
            words = words[1:]  # typed out of habit from the terminal
        try:
            command, new, named = parse_words(words, settings)
        except WordError as error:
            print(error)
            continue
        if command == "quit":
            return 0
        if new != settings:
            print(settings_table(new, before=settings))
        elif not command:
            for name in named:
                print(CHOICES[name])
        settings = new
        if not command:
            continue
        if command == "help":
            print(shell_help(settings))
            continue
        try:
            status = run_command(command, settings, folder)
        except KeyboardInterrupt:
            print("\nStopped.")
            continue
        if command == "make" and status == 0 and not told_shortcut:
            print(f"(Outside the shell, the same diary is: {command_name()} {' '.join(settings.words())})")
            told_shortcut = True


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        if not argv:
            return shell(FOLDER)
        try:
            command, settings, named = parse_words(argv, Settings())
        except WordError as error:
            print(error, file=sys.stderr)
            return 2
        if command == "quit":
            return 0
        if named and not command and settings == Settings():
            print("\n".join(CHOICES[name] for name in named))
            return 0
        return run_command(command or "make", settings, FOLDER)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
