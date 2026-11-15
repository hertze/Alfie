# Alfie -- a diary generator

This is Alfie, a Python script that makes diary inserts for ring binders (pocket, personal, A6 and A5) for any year, in Swedish, English or German. It writes a LaTeX file and typesets it with XeLaTeX.

Alfie works out the Swedish holidays and other named days for every year by itself, so all you keep up to date is a short list of your own dates.

## Getting started

In a terminal, in the Alfie folder:

    ./alfie.py install

That makes an `alfie` command that works in any folder. Then make a file for your own dates, like birthdays (see [Your dates](#your-dates)):

    alfie init

And make a diary:

    alfie 2027

That makes `diary-personal-2027-sv.pdf` with your usual settings and opens it. Without a year, you get next year's diary.

Until you've run `./alfie.py install`, type `./alfie.py` instead of `alfie`, in the Alfie folder.

## Words

Alfie takes plain words, in any order:

    alfie 2027 pocket                 pocket size
    alfie 2027 pocket save-paper      four pocket pages on each A4 sheet
    alfie 2027 wg color               the four-page week layout, in colour
    alfie list 2027                   the red days and notes it will show
    alfie 2027 from mars to april     only the leaves for March and April
    alfie help                        all the words

| Words | What they do |
| --- | --- |
| `make`, `list`, `settings`, `init`, `install`, `help` | what to do; `make` if you don't say |
| a year, like `2027` | the year; next year if you leave it out |
| `pocket`, `personal`, `a6`, `a5` | paper size |
| `w1p`, `w1pnotes`, `w2p`, `w2pwf`, `1dp`, `wg`, `w2pcolslandscape`, `w2pcolsportrait` | layout, see below |
| `sv`, `de`, `en` | language |
| `color`, `bw` | red days and notes in red, or all black |
| `save-paper`, `no-save-paper` | several pages on each A4 sheet, see [Saving paper](#saving-paper) |
| `back=+1.0`, `back=0`, `back=-0.5` | moves the back of each sheet, in mm, see [Printer adjustment](#printer-adjustment) |
| `from 15 mars`, `to 30 april`, `whole-year` | only the leaves for some dates, see [Only some dates](#only-some-dates) |
| `holidays`, `no-holidays` | the built-in Swedish calendar, on for Swedish diaries |
| `tex-only`, `pdf` | only write the LaTeX file, or typeset it as usual |
| `no-open`, `open` | whether to open the PDF afterwards |

Your usual settings are in `DEFAULTS` at the top of `alfie.py`. If Alfie doesn't know a word, it stops and suggests the closest one. `paper` or `layout` on their own list the choices. The older style with dashes, like `--paper pocket --save-paper`, still works.

Layouts:

- `w1p`: a week on one page
- `w1pnotes`: a week on one page, with a notes page after it
- `w2p`: a week on two pages
- `w2pwf`: a week on two pages, with more room for the weekdays
- `1dp`: a day per page
- `wg`: a week on four pages, with week dots, week notes and a gratitude page
- `w2pcolslandscape`: a week on two pages in columns, for a binder turned on its side, see below
- `w2pcolsportrait`: the same week in columns, for a binder held upright, see below

### The week in columns

Both column layouts put Monday, Tuesday and Wednesday side by side in three columns on the left-hand page, and Thursday, Friday, and Saturday and Sunday sharing the last column on the right-hand page. Both pages have the month and the week number at the top. The lines between the columns are as thin as the lines between the days in the other layouts.

`w2pcolslandscape` is for using the binder turned a quarter turn clockwise, so the rings run across the middle: Monday to Wednesday above the rings, Thursday to Sunday below. Each page is laid out across, and printed turned so that it reads the right way up; the title page is turned too. The turned pages keep the wide margin where the holes are and get the outer margin on the other three sides, and the lines divide the page in thirds, so the columns above and below the rings line up. A note goes beside its weekday if there's room, otherwise under it, flush right.

`w2pcolsportrait` is the same week on ordinary upright pages, with the usual margins. Its columns are narrow, so notes always go on the line under the date, flush left with the circle, where they get the whole width of the column. There's 2 mm between a column's text and the lines beside it: enough for the longest weekday (Donnerstag) and holiday word (Midsommardagen) on pocket paper.

Printing, saving paper and the printer adjustment work as for the other layouts.

### The shell

Type `alfie` on its own to get a shell. It starts by showing the settings and what they mean:

    Alfie 3.1 makes diary inserts. The settings are:

      Year       2027      next year
      Paper      personal  97 × 173 mm
      Layout     w2pwf     a week on two pages, with more room for the weekdays
      Language   sv        Swedish
      Colour     bw        black and white
      Save paper off       one page per A4 sheet
      Holidays   on        the Swedish calendar

Type a new value to change a setting, and Alfie shows what changed:

    alfie> pocket save-paper
      Paper      pocket    83 × 122 mm
      Save paper on        4 pages on each A4 sheet

Then `list` shows the red days and notes, and `make` makes the diary. `settings` shows all the settings again, `help` lists every word with the current choices marked, and `quit` (or Ctrl-D) leaves. Tab completes the words.

The settings stay until you leave, so you can list the dates, fix your dates file, list again and make the diary without starting over.

Alfie keeps its files in its own folder, next to `alfie.py`, whichever folder you run it from: your dates file, and the PDFs it makes.

## Red days

Sundays are always red. The built-in Swedish calendar adds, for any year from 2005 on:

- **Red days:** Nyårsdagen, Trettondedag jul, Långfredagen, Påskdagen, Annandag påsk, Första maj, Kristi himmelsfärd, Pingstdagen, Nationaldagen, Midsommardagen, Alla helgons dag, Juldagen and Annandag jul.
- **Named days:** Alla hjärtans dag, Skärtorsdagen, Påskafton, Annandag pingst, Mors dag, Midsommarafton, Halloween, Fars dag, Lucia, Julafton, Nyårsafton, and the days summer and winter time start.

The red days follow the Swedish holiday law, [Lag (1989:253) om allmänna helgdagar](https://data.riksdagen.se/dokument/sfs-1989-253.html), as it has stood since 2005, when Nationaldagen became a red day and Annandag pingst stopped being one. Easter is worked out from the church's calculated full moon, not the astronomical one, as the law's preparatory work says ([prop. 1988/89:114](https://lagen.nu/prop/1988/89:114)). Midsommarafton, Julafton and Nyårsafton aren't red days by law. Alfie won't use the built-in calendar for years before 2005, which had other red days; for those, add the word `no-holidays` and mark the red days yourself.

`test_alfie.py` checks every year from 2005 to 9998 against a second implementation written straight from the law's wording, and Easter against two other published algorithms. Run the tests after changing anything in the calendar:

    python3 -m unittest -v

You can change the named days in `swedish_calendar()` in `alfie.py`. The red days have to stay as the law says.

## Your dates

Your own dates go in `dates.md` or `dates.txt` in the Alfie folder. They work the same; `dates.md` is handy if you like editing it as Markdown. If both are there, Alfie reads `dates.md` and tells you it's ignoring `dates.txt`. `alfie init` writes a starter file that explains the format.

One date per line: day, month, a colon and the text. Start a line with `*` to make the day red. Dates at the top come back every year, like birthdays. Dates under a heading with a year are for that year only:

    21 januari: Annas födelsedag
    25 augusti: Bröllopsdag

    ## 2027
    * 31 december: Nyårsafton
    14 april: Tandläkare 08.30

    ## 2028
    3 mars: Flytt

A year section lasts until the next heading with a year, or `## Every year` (`## Varje år`), which goes back to dates for every year. Other lines starting with `#` are skipped, so you can use them for comments.

Lines can also be written as a Markdown list, `- 21 januari: Annas födelsedag`. A `*` at the start still means a red day, so use `-` for list items.

- Month names can be Swedish, English or German, written out or shortened to three letters (`21 jan`).
- A day can have any number of notes. They're joined with commas: red days first, then your notes, then the other built-in days.
- An every-year `29 februari` shows on 28 februari in years that don't have one.
- If a line can't be read (`31 april`, a misspelt month, a missing colon), Alfie stops and lists every such line with its file and line number.

Check what you'll get before you print:

    alfie list 2027

In the list, ● marks the red days: holidays, and days you marked with `*`. Ordinary Sundays are red in the diary too, but the list doesn't mark them.

### Week notes

The `wg` layout can print a text, such as a quote, on each week's gratitude page. Put them in `weeknotes.md` or `weeknotes.txt`, one per line, starting with the week number. Year headings work the same way as for your dates:

    1: Two roads diverged in a wood, and I--I took the one less traveled by, And that has made all the difference. --- Robert Frost
    3: Your mind is for having ideas, not holding them. --- David Allen

## Only some dates

To print part of the year again, or to fix a few weeks in a diary you've already printed, give the dates:

    alfie 2027 from 15 mars to 30 april
    alfie 2027 from mars to april
    alfie 2027 pocket save-paper from 2027-03-15 to 2027-04-30

A date is a day and a month (`15 mars`, `15mars`, `15 march`), a month on its own (from its first day, or to its last), or a full date like `2027-03-15`, which is also how to reach the days of the neighbouring years at the start and end of the diary. Leave out `from` or `to` to start at the beginning of the year or go on to its end. In the shell the dates stay until you change them; `whole-year` goes back to all of it.

Alfie makes the whole year as usual and keeps only the pages with those days, so every page is exactly as it is in the whole year's diary, on the same side and in the same place. It keeps whole leaves, since a leaf is printed on both sides: if the first day is on a left-hand page, the right-hand page before it comes too, and if the last day is on a right-hand page, so does the left-hand page on its back. That gives a few days more than you asked for. Alfie says which pages you get and which leaves of the whole diary they replace, counting the title page as leaf 1:

    Pages 23–38 of 107, with 11 mars to 5 maj: whole leaves, so a few days more than you asked for.
    They replace leaves 12–19 of the whole diary, counting the title page as leaf 1.

It works with one page per sheet and with `save-paper`; the file is called like `diary-personal-2027-sv-03-15-to-04-30.pdf`. `list` with dates shows only the red days and notes for those days.

## Saving paper

Normally every diary page gets its own A4 sheet, with crop marks around it. With the word `save-paper`, Alfie puts several pages on each sheet instead:

| Paper | Pages on each side of an A4 sheet | 2027 diary (w2pwf) |
| --- | --- | --- |
| `pocket` | 4 | 14 sheets instead of 54 |
| `personal` | 2, turned on their side | 27 sheets instead of 54 |
| `a6` | 2, turned on their side | 27 sheets instead of 54 |
| `a5` | doesn't fit, so one page per sheet as usual | |

The file is called `diary-pocket-2027-sv-4up.pdf` (or `-2up`). To print and cut it:

1. Print it two-sided, flipping on the long edge (the usual two-sided setting), at 100 % size, not "fit to page".
2. Cut along the crop marks. Every page corner has a cross whose arms run along the page's edges, both outwards and in towards the middle of the page, so every piece you cut off still shows where its remaining edges are.
3. Put pile A on top of pile B (on top of C and D for pocket). The leaves are then in order. The pile letters and the instructions are printed in the margin that gets cut off.

Each page's back is printed right behind it, the right way up. To check your printer's setting before printing everything, print the first sheet only, cut out the title page and turn it over: the first week should be on the back, the right way up.

## Printer adjustment

Many printers don't print the back of a sheet exactly behind the front. If yours prints the back higher, Alfie can move everything on the back of each sheet down to make up for it, both with one page per sheet and when saving paper. The fronts, with the crop marks you cut along, stay where they are.

The usual setting is `back=+1.0`: the back moves 1.0 mm down. Use `back=-0.5` to move it 0.5 mm up instead, or `back=0` to leave it. Decimals can be written with a comma too (`back=+0,9`). To change the usual value, set `back_offset` in `DEFAULTS` at the top of `alfie.py`.

To find the right value, print a sheet two-sided, hold it against a window and see how far the back's lines are from the front's.

## Output

The PDF ends up in the Alfie folder. LaTeX works in a `build/` folder, which Alfie removes after a successful run, so only the PDF is left. With `tex-only`, the LaTeX file stays in `build/`.

If XeLaTeX fails, Alfie shows the error and where to find the full log, keeps `build/` so you can read it, and doesn't open an old PDF.

## Requirements

- Python 3.9 or later
- XeLaTeX, for example from [MacTeX](https://tug.org/mactex/)
- The Cronos Pro font family
