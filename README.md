# Alfie -- a diary generator

This is Alfie, a python script capable of generating diary inserts in pocket, personal or A5 size of any year you want. The script in itself makes a LaTeX file ready for typesetting.

Right now, Alfie can make diaries in Swedish and English. It can render holidays and date-specific notes, as listed in used-provided text files. It can also add front and back matter, as supplied by supplementary files.

## Manual

This script needs a few arguments to run:

1. The format you want (pocket/personal/a5)

2. The language you want (sv/en)

3. The year you want

4. Whether it should include a frontmatter (yes/no)

5. Whether it should include a backmatter (yes/no)

6. Whether it should try to typeset the resulting LaTeX file (yes/no)

If you launch the script without arguments, it will run with a minimal text interface, taking you through some questions.

Run it like this:

> python3 alfie.py`

If you run it with an argument, it will run *without* any interface whatsoever. You need to use the following syntax for the argument to work:
    
> python3 alfie.py <format>-<language>-<year>-<frontmatter>-<backmatter>-<typeset?>
For example:

> `python3 alfie.py personal-en-2014-no-no-yes`

will make a Swedish LaTeX diary for 2014 in personal size and then typeset it.

