# Alfie -- a diary generator

This is Alfie, a Python script that makes diary inserts for ring binders (pocket, personal, A6 and A5) for any year, in Swedish, English or German. It writes a LaTeX file and typesets it with XeLaTeX.

Alfie works out the Swedish holidays and other named days for every year by itself, so all you keep up to date is a short list of your own dates.

## Quick start

From the terminal, in the Alfie folder. On a new install, start by making a file for your own dates (see [Red days and notes](#red-days-and-notes)):

    ./alfie.py --init

Then:

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
| `--save-paper` | puts several pages on each A4 sheet, see [Saving paper](#saving-paper) | off |
| `--holidays` | `se` (the built-in Swedish calendar) or `none` | `se` for Swedish, otherwise `none` |
| `--init` | writes a starter `dates.txt` to fill in (never overwrites your dates) | |
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
    ./alfie.py 2027 --paper pocket --save-paper
    ./alfie.py 2027 --list

## Red days and notes

Sundays are always red. The built-in Swedish calendar adds, for any year from 2005 on:

- **Red days:** Nyårsdagen, Trettondedag jul, Långfredagen, Påskdagen, Annandag påsk, Första maj, Kristi himmelsfärd, Pingstdagen, Nationaldagen, Midsommardagen, Alla helgons dag, Juldagen and Annandag jul.
- **Named days:** Alla hjärtans dag, Skärtorsdagen, Påskafton, Annandag pingst, Mors dag, Midsommarafton, Halloween, Fars dag, Lucia, Julafton, Nyårsafton, and the days summer and winter time start.

The red days follow the Swedish holiday law, [Lag (1989:253) om allmänna helgdagar](https://data.riksdagen.se/dokument/sfs-1989-253.html), as it has stood since 2005, when Nationaldagen became a red day and Annandag pingst stopped being one. Easter is worked out from the church's calculated full moon, not the astronomical one, as the law's preparatory work says ([prop. 1988/89:114](https://lagen.nu/prop/1988/89:114)). Midsommarafton, Julafton and Nyårsafton aren't red days by law. Alfie won't use the built-in calendar for years before 2005, which had other red days.

`test_alfie.py` checks every year from 2005 to 9998 against a second implementation written straight from the law's wording, and Easter against two other published algorithms. Run the tests after changing anything in the calendar:

    python3 -m unittest -v

You can change the named days in `swedish_calendar()` in `alfie.py`. The red days have to stay as the law says.

Your own dates go in `dates.txt` or `dates.md`, in the folder you run Alfie from. They work the same; use `dates.md` if you like editing it as Markdown. If both are there, Alfie reads `dates.md` and tells you it's ignoring `dates.txt`. To get a starter file that explains the format:

    ./alfie.py --init

One date per line: day, month, a colon and the text. Start a line with `*` to make the day red. Dates at the top come back every year, like birthdays. Dates under a heading with a year are for that year only:

    21 januari: Annas födelsedag
    25 augusti: Bröllopsdag

    ## 2027
    * 31 december: Nyårsafton
    14 april: Tandläkare 08.30

    ## 2028
    3 mars: Flytt

A year section lasts until the next heading with a year, or `## Every year` (`## Varje år`), which goes back to dates for every year. Other lines starting with `#` are skipped, so you can use them for comments.

Lines can also be written as a Markdown list, `- 21 januari: Annas födelsedag`. Note that a `*` at the start still means a red day, so use `-` for list items.

- Month names can be Swedish, English or German, written out or shortened to three letters (`21 jan`).
- A day can have any number of notes. They're joined with commas: red days first, then your notes, then the other built-in days.
- An every-year `29 februari` shows on 28 februari in years that don't have one.
- If a line can't be read (`31 april`, a misspelt month, a missing colon), Alfie stops and lists every such line with its file and line number.

Check what you'll get before you print:

    ./alfie.py 2027 --list

In the list, ● marks the red days: holidays, and days you marked with `*`. Ordinary Sundays are red in the diary too, but the list doesn't mark them.

### Week notes

The `wg` layout can print a text, such as a quote, on each week's gratitude page. Put them in `weeknotes.txt` (or `weeknotes.md`), one per line, starting with the week number. Year headings work the same way as for your dates:

    1: Two roads diverged in a wood, and I--I took the one less traveled by, And that has made all the difference. --- Robert Frost
    3: Your mind is for having ideas, not holding them. --- David Allen

## Saving paper

Normally every diary page gets its own A4 sheet, with crop marks around it. With `--save-paper`, Alfie puts several pages on each sheet instead:

| Paper | Pages on each side of an A4 sheet | 2027 diary (w2pwf) |
| --- | --- | --- |
| `pocket` | 4 | 14 sheets instead of 54 |
| `personal` | 2, turned on their side | 27 sheets instead of 54 |
| `a6` | 2, turned on their side | 27 sheets instead of 54 |
| `a5` | doesn't fit, so one page per sheet as usual | |

The file is called `diary-pocket-2027-sv-4up.pdf` (or `-2up`). To print and cut it:

1. Print it two-sided, flipping on the long edge (the usual two-sided setting), at 100 % size, not "fit to page".
2. Cut the whole pile along the crop marks.
3. Put pile A on top of pile B (on top of C and D for pocket). The leaves are then in order. The pile letters and the instructions are printed in the margin that gets cut off.

Each page's back is printed right behind it, the right way up. To check your printer's setting before printing everything, print the first sheet only, cut out the title page and turn it over: the first week should be on the back, the right way up.

## Output

The PDF ends up in the folder you run Alfie from. LaTeX works in a `build/` folder, which Alfie removes after a successful run, so only the PDF is left. With `--tex-only`, the LaTeX file stays in `build/`.

If XeLaTeX fails, Alfie shows the error and where to find the full log, keeps `build/` so you can read it, and doesn't open an old PDF.

## Requirements

- Python 3.9 or later
- XeLaTeX, for example from [MacTeX](https://tug.org/mactex/)
- The Cronos Pro font family
