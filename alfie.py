#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# A L F I E
# version 3.0
#
# by Joakim Hertze
#
# Makes diary inserts for ring binders as LaTeX and typesets them with XeLaTeX.
#
#   ./alfie.py 2027          the 2027 diary, with the defaults below
#   ./alfie.py 2027 --list   the red days and notes it will show
#   ./alfie.py               asks step by step
#   ./alfie.py --help        all options

from __future__ import annotations

import argparse
import calendar
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
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
}
AUTHOR = "Joakim Hertze"

# Files Alfie reads from the folder you run it in.
NOTES_FILE = "notes.txt"                      # your dates, every year
YEAR_NOTES_FILE = "notes-{year}.txt"          # your dates, one year only
WEEKNOTES_FILE = "weeknotes.txt"              # week notes (layout wg), every year
YEAR_WEEKNOTES_FILE = "weeknotes-{year}.txt"  # week notes (layout wg), one year only

# The PDF ends up in the folder you run Alfie in. The LaTeX file and
# XeLaTeX's working files (.aux, .log, .out) go in this subfolder.
BUILD_DIR = "build"

LAYOUTS = {
    "w1p": "a week on one page",
    "w1pnotes": "a week on one page, with a notes page after it",
    "w2p": "a week on two pages",
    "w2pwf": "a week on two pages, with more room for the weekdays",
    "1dp": "a day per page",
    "wg": "a week on four pages, with week dots, week notes and a gratitude page",
}

PAPERS = {  # millimetres
    "pocket": {"width": "83", "height": "122", "margin": "4", "left": "12", "top": "3", "bottom": "4"},
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
    """(date, name, red day?) for one year. Edit this list to change what's built in."""
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

# ---------------------------------------------------------------------------
# Your notes: notes.txt, notes-YEAR.txt, weeknotes.txt, weeknotes-YEAR.txt
# ---------------------------------------------------------------------------

# The order texts are listed in when a day has several:
# red days first, then your own notes, then the other built-in days.
RANK_RED, RANK_YOURS, RANK_BUILT_IN = 0, 1, 2

NOTE_LINE = re.compile(r"(\*)?\s*(\d{1,2})\.?\s+([^\W\d_]+)\.?\s*(?::(.*))?")
WEEKNOTE_LINE = re.compile(r"(\d{1,2})\s*:(.*)")
OLD_FILE = re.compile(r"(holidays|notes|weeknotes)-\d{4}-[a-z]{2}\.txt")


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
    """(line number, text) for every line that isn't empty or a # comment."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        problems.append(f"{path.name}: please save it as UTF-8 text")
        return []
    lines = [(number, line.strip()) for number, line in enumerate(text.splitlines(), start=1)]
    return [(number, line) for number, line in lines if line and not line.startswith("#")]


def read_notes(path, year, problems):
    """[(month, day, text, red)] from a notes file. year is None for notes.txt (every year)."""
    notes = []
    for number, line in read_lines(path, problems):
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
            date(year or 2000, month, int(day))  # 2000 was a leap year, so 29 februari is fine in notes.txt
        except ValueError:
            problems.append(f"{where}: there is no {int(day)} {month_name}" + (f" in {year}" if year else ""))
            continue
        if not text and not star:
            problems.append(f"{where}: nothing after the date (start the line with * to only make the day red)")
            continue
        notes.append((month, int(day), text, bool(star)))
    return notes


def read_weeknotes(path, problems):
    """[(week number, text)] from a week notes file."""
    notes = []
    for number, line in read_lines(path, problems):
        where = f"{path.name}, line {number}"
        match = WEEKNOTE_LINE.fullmatch(line)
        if not match or not match.group(2).strip():
            problems.append(f"{where}: expected '<week number>: <text>'")
        elif not 1 <= int(match.group(1)) <= 53:
            problems.append(f"{where}: there is no week {int(match.group(1))}")
        else:
            notes.append((int(match.group(1)), match.group(2).strip()))
    return notes


def load_notes(year, holidays, folder, weeknotes=False):
    """Red days and notes for every date in the diary. The diary begins and ends with a few
    days of the neighbouring years, so those years are worked out too.
    Raises NotesError listing every line that can't be used."""
    problems, files, days = [], [], {}

    def add(day, text, red, rank):
        days.setdefault(day, DayInfo()).add(text, red, rank)

    every_year = []
    path = folder / NOTES_FILE
    if path.exists():
        every_year = read_notes(path, None, problems)
        files.append(f"{path.name} ({plural(len(every_year), 'note')})")

    for this_year in (year - 1, year, year + 1):
        for day, name, red in HOLIDAY_CALENDARS[holidays](this_year):
            add(day, name, red, RANK_RED if red else RANK_BUILT_IN)
        for month, day, text, red in every_year:
            if (month, day) == (2, 29) and not calendar.isleap(this_year):
                day = 28  # a note on 29 februari shows on 28 februari in other years
            add(date(this_year, month, day), text, red, RANK_RED if red else RANK_YOURS)
        path = folder / YEAR_NOTES_FILE.format(year=this_year)
        if path.exists():
            notes = read_notes(path, this_year, problems)
            for month, day, text, red in notes:
                add(date(this_year, month, day), text, red, RANK_RED if red else RANK_YOURS)
            if this_year == year:
                files.append(f"{path.name} ({plural(len(notes), 'note')})")

    week_texts = {}
    if weeknotes:
        for path in (folder / WEEKNOTES_FILE, folder / YEAR_WEEKNOTES_FILE.format(year=year)):
            if path.exists():
                notes = read_weeknotes(path, problems)
                for week, text in notes:
                    week_texts.setdefault(week, []).append(text)
                files.append(f"{path.name} ({plural(len(notes), 'week note')})")

    if problems:
        raise NotesError(problems)
    return Notes(days, week_texts, files)


def warn_about_old_files(folder):
    old = sorted(path.name for path in folder.iterdir() if OLD_FILE.fullmatch(path.name))
    if old:
        print(f"Note: {', '.join(old)} {'is' if len(old) == 1 else 'are'} in the old format and no longer read.\n"
              f"      Holidays are built in now. Your own dates go in {NOTES_FILE} or "
              f"{YEAR_NOTES_FILE.format(year='YEAR')}; see README.md.")

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


class Diary:
    def __init__(self, year, paper, color, layout, language, notes):
        self.year = year
        self.paper = paper
        self.color = color
        self.layout = layout
        self.strings = LANGUAGES[language]
        self.notes = notes

    def latex(self):
        layouts = {
            "w1p": self.week_on_one_page,
            "w1pnotes": self.week_with_notes_page,
            "w2p": lambda: self.week_on_two_pages(top_stretch=1, weekend_stretch=1),
            "w2pwf": lambda: self.week_on_two_pages(top_stretch=0.2, weekend_stretch=0.6),
            "1dp": self.day_per_page,
            "wg": self.week_gold,
        }
        return self.preamble() + self.opening() + layouts[self.layout]() + "\\end{document}\n\n"

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

    def preamble(self):
        paper = PAPERS[self.paper]
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
            "\\usepackage[dvips=false,pdftex=false,vtex=false,twoside]{geometry}",
            "\\usepackage[cross,a4,center,dvips,noinfo,odd]{crop}",
            "\\defaultfontfeatures{Mapping=tex-text}",
            "\\setmainfont[BoldFont=Cronos Pro, ItalicFont=Cronos Pro Light Italic, "
            "BoldItalicFont=Cronos Pro Semibold, SlantedFont=Cronos Pro Bold, SmallCapsFont=Cronos Pro Light, "
            "SmallCapsFeatures={LetterSpace=1.15, Letters=SmallCaps}, Numbers={OldStyle, Proportional}, "
            "Scale=0.75] {Cronos Pro Light}",
            f"\\geometry{{paperwidth={paper['width']}mm, paperheight={paper['height']}mm, "
            f"margin={paper['margin']}mm, bottom={paper['bottom']}mm, top={paper['top']}mm, "
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
        return "\n".join(lines)

    def opening(self):
        s = self.strings
        title = s["title"].format(paper=self.paper.title())
        return (
            "\\begin{document}\n\n"
            f"\\title{{\\bfseries\\itshape \\Huge {s['the_year']} {self.year}\\\\ "
            f"\\vspace{{0.25em}} \\Large \\normalfont {title}}}\n"
            f"\\author{{\\emph{{{s['by']}}} {AUTHOR}}}\n"
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

    def format_day(self, day, recto):
        """The date in a circle, the weekday and any notes. Red days get a filled circle and
        italics, Saturdays a black circle. On right-hand (recto) pages the date goes right."""
        note = latex_escape(self.note(day))
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
        name = "\\normalfont\\normalsize " + self.day_name(day)
        if recto:
            text = "\\hfill " + style + name + " \\hspace{0mm} " + circle
            if note:
                text = "\\small \\notescolor{" + note + "} " + text
        else:
            text = style + circle + " \\hspace{0mm} " + name
            if note:
                text += "\\hfill \\small \\notescolor{" + note + "}"
        return text + "\n\n"

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

    # --- Checking

    def print_list(self):
        print(f"\nRed days (●) and notes for {self.year}:\n")
        for day in sorted(day for day in self.notes.days if day.year == self.year):
            info = self.notes.days[day]
            if info.text or info.red:
                mark = "●" if self.is_red(day) else " "
                print(f"{day.day:>3} {self.month_name(day)[:3]} {self.day_name(day)[:3]}  {mark} {info.text}")

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


def typeset(tex, out_folder):
    """Run XeLaTeX on the .tex file and move the PDF to out_folder. Returns the PDF, or None."""
    xelatex = shutil.which("xelatex") or (MACTEX_XELATEX if os.path.exists(MACTEX_XELATEX) else None)
    if not xelatex:
        print("I can't find XeLaTeX. Install MacTeX, or use --tex-only to just write the LaTeX file.",
              file=sys.stderr)
        return None
    built = tex.with_suffix(".pdf")
    built.unlink(missing_ok=True)
    print("Typesetting with XeLaTeX ...")
    result = subprocess.run(
        [xelatex, "-interaction=nonstopmode", "-halt-on-error", tex.name],
        cwd=tex.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace",
    )
    if result.returncode != 0 or not built.exists():
        log = tex.with_suffix(".log")
        print("\nXeLaTeX stopped with an error:\n", file=sys.stderr)
        print(latex_error(log, result.stdout), file=sys.stderr)
        print(f"\nThe whole log is in {log}", file=sys.stderr)
        return None
    pdf = out_folder / built.name
    os.replace(built, pdf)
    return pdf

# ---------------------------------------------------------------------------
# Command line and questions
# ---------------------------------------------------------------------------


def next_year():
    return date.today().year + 1


def year_argument(text):
    if re.fullmatch(r"\d{4}", text) and 1583 <= int(text) <= 9998:
        return int(text)
    if "-" in text:
        raise argparse.ArgumentTypeError(
            f"'{text}' is the old way of giving options. Now it's e.g. "
            "./alfie.py 2027 --paper pocket --layout wg (see --help)")
    raise argparse.ArgumentTypeError(f"'{text}' isn't a year (four digits, like {next_year()})")


def parse_arguments(argv):
    parser = argparse.ArgumentParser(
        prog="alfie.py",
        description="Makes a diary insert as LaTeX and typesets it with XeLaTeX. "
                    "Run it without arguments to be asked step by step.",
        epilog="Layouts: " + "; ".join(f"{name} = {text}" for name, text in LAYOUTS.items())
               + ". Red days and notes: see README.md.",
    )
    parser.add_argument("year", nargs="?", type=year_argument, default=next_year(),
                        help="the year (default: next year, %(default)s)")
    parser.add_argument("--paper", choices=PAPERS, default=DEFAULTS["paper"],
                        help="paper size (default: %(default)s)")
    parser.add_argument("--layout", choices=LAYOUTS, default=DEFAULTS["layout"],
                        help="page layout, see below (default: %(default)s)")
    parser.add_argument("--lang", dest="language", choices=LANGUAGES, default=DEFAULTS["language"],
                        help="language (default: %(default)s)")
    colors = parser.add_mutually_exclusive_group()
    colors.add_argument("--color", dest="color", action="store_const", const="color",
                        help="red days and notes in red" + (" (default)" if DEFAULTS["color"] == "color" else ""))
    colors.add_argument("--bw", dest="color", action="store_const", const="bw",
                        help="black and white" + (" (default)" if DEFAULTS["color"] == "bw" else ""))
    parser.set_defaults(color=DEFAULTS["color"])
    parser.add_argument("--holidays", choices=HOLIDAY_CALENDARS,
                        help="built-in red days and named days (default: se for Swedish, otherwise none)")
    parser.add_argument("--list", action="store_true",
                        help="show the year's red days and notes instead of making the diary")
    parser.add_argument("--tex-only", action="store_true", help="write the LaTeX file but don't typeset it")
    parser.add_argument("--no-open", action="store_true", help="don't open the PDF afterwards")
    return parser.parse_args(argv)


def ask(question, options, default):
    while True:
        answer = input(f"\n> {question} ({'/'.join(options)})? [{default}] ").strip().lower()
        if not answer:
            return default
        if answer in options:
            return answer
        print(f"Please choose one of: {', '.join(options)}")


def ask_year(default):
    while True:
        answer = input(f"\n> What year do you need (YYYY)? [{default}] ").strip()
        if not answer:
            return default
        try:
            return year_argument(answer)
        except argparse.ArgumentTypeError as error:
            print(error)


def shortcut(args):
    """The command that makes the same diary without the questions."""
    words = ["./alfie.py", str(args.year)]
    if args.paper != DEFAULTS["paper"]:
        words += ["--paper", args.paper]
    if args.layout != DEFAULTS["layout"]:
        words += ["--layout", args.layout]
    if args.language != DEFAULTS["language"]:
        words += ["--lang", args.language]
    if args.color != DEFAULTS["color"]:
        words.append(f"--{args.color}")
    if args.tex_only:
        words.append("--tex-only")
    return " ".join(words)


def ask_questions():
    print("\n\nA L F I E\n\nA somewhat clever diary generator for Filofax-sized binders")
    print("\n---------------------------------------------------------\n")
    print("\nHello,")
    print("\nI have some questions before we begin:")
    args = argparse.Namespace(holidays=None, list=False, no_open=False)
    args.paper = ask("What format should I use for your insert", list(PAPERS), DEFAULTS["paper"])
    args.color = ask("Should I use color or black & white mode", ["color", "bw"], DEFAULTS["color"])
    args.layout = ask("What layout should I use for your insert", list(LAYOUTS), DEFAULTS["layout"])
    args.language = ask("What language should I use", list(LANGUAGES), DEFAULTS["language"])
    args.year = ask_year(next_year())
    args.tex_only = ask("Shall I typeset it to PDF as well", ["yes", "no"], "yes") == "no"
    print(f"\nNext time you can skip the questions: {shortcut(args)}\n")
    return args


def make_diary(args, folder):
    holidays = args.holidays or ("se" if args.language == "sv" else "none")
    warn_about_old_files(folder)
    try:
        notes = load_notes(args.year, holidays, folder, weeknotes=args.layout == "wg")
    except NotesError as error:
        print("Please fix these lines first:\n" + "\n".join(f"  {problem}" for problem in error.problems),
              file=sys.stderr)
        return 1

    print("Built-in calendar: " + ("Swedish" if holidays == "se" else "none (only Sundays are red)"))
    print("Your notes: " + (", ".join(notes.files) if notes.files
                            else f"none (no {NOTES_FILE} or {YEAR_NOTES_FILE.format(year=args.year)})"))
    diary = Diary(args.year, args.paper, args.color, args.layout, args.language, notes)
    if args.list:
        diary.print_list()
        return 0

    print(f"Making the {args.year} diary: {args.paper}, {args.layout}, {args.language}, {args.color}")
    build = folder / BUILD_DIR
    build.mkdir(exist_ok=True)
    tex = build / f"diary-{args.paper}-{args.year}-{args.language}.tex"
    tex.write_text(diary.latex(), encoding="utf-8")
    print(f"Wrote {tex.relative_to(folder)}")
    if args.tex_only:
        return 0

    pdf = typeset(tex, folder)
    if pdf is None:
        return 1
    print(f"Done: {pdf.name}")
    if not args.no_open and sys.platform == "darwin":
        subprocess.run(["open", str(pdf)], check=False)
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    interactive = not argv
    try:
        args = ask_questions() if interactive else parse_arguments(argv)
        status = make_diary(args, Path.cwd())
    except (KeyboardInterrupt, EOFError):
        print("\nStopped.")
        return 130
    if interactive and status == 0:
        print("\n\nAll done!")
        print("\n\n---------------------------------------------------------\n\n")
    return status


if __name__ == "__main__":
    sys.exit(main())
