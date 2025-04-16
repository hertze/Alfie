# Alfie -- a diary generator

This is Alfie, a python script capable of generating diary inserts in pocket, personal or A5 size of any year you want. The script in itself makes a LaTeX file ready for typesetting and can try to typeset it for you if you have XeLateX installed on your system.

Right now, Alfie can make diaries in Swedish, English and German. It can render holidays and date-specific notes, as listed in used-provided text files. It can also add front and back matter, as supplied by supplementary files.

If you want to use the script “out of the box” you need the free Adobe Source Sans Pro font installed on your machine. You can of course use whatever font you like, but I find Source Sans Pro Light to be ideal for this kind of thing. You also need to have LaTeX installed in order to typeset the resulting LaTeX-files

## Manual

### Running the script

From the terminal (on a Mac), run the script with `python3 alfie.py`.

The script will as you a series of questions:

1. The format you want (pocket / personal / a6 / a5)

2. If you want your diary in color or black and white (color / bw)

3. The layout you want (w1p = 1 week per page / w1pnotes = week on one page with notes / w2p = week on two pages / w2pwf = week on two pages with emphasis on weekdays / 1dp = day per page / wg = extra everything)

4. The language you want (sv / de / en)

5. The year you want

6. Whether it should try to typeset the resulting LaTeX file (yes / no)

Answers to those questions can be passed as arguments and thus bypass the text interface. IYou need to use the following syntax for the argument to work:
    
> `python3 alfie.py <format>-<color>-<layout>-<language>-<year>-<typeset>`

For example:

> `python3 alfie.py personal-color-w2p-sv-2014-yes`

will make a Swedish LaTeX diary for 2014 in personal size and then typeset it.

### Holidays, notes and week notes

At runtime, Alfie will look for two text files, **notes-<year>.txt** (i.e. notes-2025.txt for the year of 2025) and **holidays-<year>.txt** (i.e. holidays-2025.txt for the year 2025). The first file has a list of dates that should be considered holidays and get a black (or red) circle around the day. For example:

    1 januari
    6 januari
    15 april
    17 april
    18 april
    1 maj

The second file adds text information for specific days, like this:

    1 januari: Nyårsdagen
    6 januari: Trettondedag jul
    14 februari: Alla hjärtans dag
    30 mars: Sommartid börjar
    17 april: Skärtorsdagen
    18 april: Långfredagen
    20 april: Påskdagen

There is a third file, **weeknotes-<year>.txt**, that holds additional text content for the layout **weekgold**, such as inspirational quotes. Here's an example, where the preceding number equals the week number where the text should be added:

    1: Two roads diverged in a wood, and I--I took the one less traveled by, And that has made all the difference. --- Robert Frost

    2: In this very moment, will you accept the sad and the sweet, hold lightly stories about what’s possible, and be the author of a life that has meaning and purpose for you, turning in kindness back to that life when you find yourself moving away from it? --- Kelly G. Wilson

    3: Your mind is for having ideas, not holding them. --- David Allen