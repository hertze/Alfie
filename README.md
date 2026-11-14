# Alfie -- a diary generator

This is Alfie, a Python script that makes diary inserts for ring binders (pocket, personal, A6 and A5) for any year, in Swedish, English or German. It writes a LaTeX file and typesets it with XeLaTeX.

Alfie works out the Swedish holidays and other named days for every year by itself, so all you keep up to date is a short list of your own dates.

## Quick start

From the terminal, in the Alfie folder:

    ./alfie.py 2027

makes `diary-personal-2027-sv.pdf` with your default settings and opens it. If you leave out the year, you get next year's diary.

Run `./alfie.py` with no arguments at all to be asked step by step instead. At the end it shows the command that makes the same diary without the questions.

## Options

| Option | What it does | Default |
| --- | --- | --- |
| *year* | four digits | next year |
| `--paper` | `pocket`, `personal`, `a6` or `a5` | `personal` |
| `--layout` | see below | `w2pwf` |
| `--lang` | `sv`, `de` or `en` | `sv` |
| `--color` / `--bw` | red days and notes in red, or all black | `--bw` |
| `--holidays` | `se` (the built-in Swedish calendar) or `none` | `se` for Swedish, otherwise `none` |
| `--list` | shows the year's red days and notes instead of making the diary | |
| `--tex-only` | writes the LaTeX file but doesn't typeset it | |
| `--no-open` | doesn't open the PDF afterwards | |

The defaults, and the name on the title page, are at the top of `alfie.py`. `./alfie.py --help` lists all of this too.

Layouts:

- `w1p`: a week on one page
- `w1pnotes`: a week on one page, with a notes page after it
- `w2p`: a week on two pages
- `w2pwf`: a week on two pages, with more room for the weekdays
- `1dp`: a day per page
- `wg`: a week on four pages, with week dots, week notes and a gratitude page

Examples:

    ./alfie.py 2027 --paper pocket
    ./alfie.py 2027 --layout wg --color
    ./alfie.py 2027 --list

## Red days and notes

Sundays are always red. The built-in Swedish calendar adds, for any year:

- **Red days:** Nyårsdagen, Trettondedag jul, Långfredagen, Påskdagen, Annandag påsk, Första maj, Kristi himmelsfärd, Pingstdagen, Nationaldagen, Midsommardagen, Alla helgons dag, Juldagen and Annandag jul.
- **Named days:** Alla hjärtans dag, Skärtorsdagen, Påskafton, Annandag pingst, Mors dag, Midsommarafton, Halloween, Fars dag, Lucia, Julafton, Nyårsafton, and the days summer and winter time start.

To change that list, edit `swedish_calendar()` in `alfie.py`.

Your own dates go in plain text files in the folder you run Alfie from:

- `notes.txt`: dates that come back every year, like birthdays. You write it once.
- `notes-2027.txt`: dates for 2027 only. Optional.

One date per line: day, month, a colon and the text. Start a line with `*` to make the day red. Lines starting with `#` are skipped.

    # notes.txt
    21 januari: Annas födelsedag
    25 augusti: Bröllopsdag

    # notes-2027.txt
    * 31 december: Nyårsafton
    14 april: Tandläkare 08.30

- Month names can be Swedish, English or German, written out or shortened to three letters (`21 jan`).
- A day can have any number of notes. They're joined with commas: red days first, then your notes, then the other built-in days.
- A `29 februari` in `notes.txt` shows on 28 februari in years that don't have one.
- If a line can't be read (`31 april`, a misspelt month, a missing colon), Alfie stops and lists every such line with its file and line number.

Check what you'll get before you print:

    ./alfie.py 2027 --list

### Week notes

The `wg` layout can print a text, such as a quote, on each week's gratitude page. Put them in `weeknotes.txt` (every year) or `weeknotes-2027.txt` (2027 only), one per line, starting with the week number:

    1: Two roads diverged in a wood, and I--I took the one less traveled by, And that has made all the difference. --- Robert Frost
    3: Your mind is for having ideas, not holding them. --- David Allen

## Output

The PDF ends up in the folder you run Alfie from. The LaTeX file and XeLaTeX's working files go in `build/`. Git ignores both.

If XeLaTeX fails, Alfie shows the error and where to find the full log, and doesn't open an old PDF.

## Requirements

- Python 3.9 or later
- XeLaTeX, for example from [MacTeX](https://tug.org/mactex/)
- The Cronos Pro font family
