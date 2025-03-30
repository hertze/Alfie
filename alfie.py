#! /usr/bin/env python3.5
# -*- coding: utf-8 -*-

# A L F I E
# version 2.0
#
# by Joakim Hertze

import calendar
import datetime
import re
import sys
import os

# Some functions

def readfile(name): # Reads a file and makes it into a list line by line
    try:
        n = []
        f = open(name, "r")
        for i in f:
            n.append(i)
        return n
    except:
        if len(sys.argv) < 2: # Only feedback is script is run without arguments
            print ("\n--> I cannot load " + name + ", but I'll probably manage without it.")
        return False

def spliceyear(vecka): # Chunk up the year
    c = calendar.LocaleTextCalendar(locale='sv_SE')
    for wholeyear in c.yeardatescalendar(year, 1):
        for months in wholeyear:
            for weeks in months:
                dennavecka = []
                # Här kommer en vecka i taget #
                for days in weeks:
                    d = datetime.date
                    dt = d.timetuple(days)
                    
                    weeknumber = d.isocalendar(days)
                    curryear = dt[0]
                    month = monthname[dt[1]-1]
                    datum = dt[2]
                    weekday = dayname[dt[6]]
                    veckonummer = weeknumber[1]
                
                    dennavecka.append([month, veckonummer, datum, weekday, curryear])
                vecka.append(dennavecka)
    return vecka
    
def purge(vecka): # Remove duplicate weeks
    purged = []
    a = 0
    b = 0
    w = 0
    for i, m in enumerate(vecka):
        a = m[0][1]
        if i > 0:
            b = vecka[i-1][0][1]
            if a != b:
                purged.append(m)
        else:
           purged.append(m)  
    return purged

def getvecka(dagar): # Gets the current week and converts it to a string
    vecka = dagar[1]
    return str(vecka)
    
def getheader(envecka): # Builds the date header for each page
    month = envecka[0][0] # Plockar månad och år från första och sista dagen av de som skickats till funktionen.
    month2 = envecka[-1][0]
    year = str(envecka[0][4])
    year2 = str(envecka[-1][4])
    if month != month2:
        if year != year2:
            header = month + " " + year + "--" + month2 + " " + year2
        else:
            header = month + "--" + month2 + " " + year
    else:
        header = month + " " + year
    return str(header)
    
    
def getheadersingle(envecka): # Builds the date header for each page
    month = envecka[0][0] # Plockar månad och år från första och sista dagen av de som skickats till funktionen.
    year = str(envecka[0][4])
    header = month + " " + year
    return str(header)
    
def holiday(dagar):  # Is this day a holiday?
    # Check if the day is Sunday or in the holidays list
    if str(dagar[3]) == sunday:  # Only Sunday is treated as a holiday
        return True
    else:
        idag = str(dagar[2]) + " " + str(dagar[0])
        if holidays:
            for line in holidays:
                if idag == line.rstrip():
                    return True
    return False  # Saturday is no longer treated as a holiday
                
def notat(dagar): # Checks if there is a note for the current day
    notat = ""
    idag = str(dagar[2]) + " " + str(dagar[0])
    if notes != False:
        for line in notes:
            line = line.split(": ")
            if idag == line[0]:
                notat = line[1]
    return notat
    
def weeknotat(dennavecka): # Checks if there is a note for the current week
    weeknotat = ""
    if weeknotes != False:
        for line in weeknotes:
            line = line.split(": ")
            if dennavecka == line[0]:
                weeknotat = line[1]
    return weeknotat

    
def format_day(dagar, notattext, is_saturday=False):
    # Start building the LaTeX string
    result = "\\large\\bfseries "
    
    # Add the appropriate circle formatting based on day type
    if is_saturday:  # Saturday (always black circle)
        # Use explicit black-filled circle for Saturdays
        result += "\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=0.1pt,minimum height=4.55mm,minimum width=4.55mm, line width=0.1pt, fill=black] (char) {\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}};}  "
    elif holiday(dagar):  # Holiday or Sunday
        result += "\\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} "
        result = result.replace("\\large\\bfseries", "\\large\\bfseries\\itshape")
    else:  # Regular weekday
        result += "\\circled{" + str(dagar[2]) + "} "
    
    # Add the day name and any notes
    result += "\\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3])
    
    # Add notes if present - now with potential color
    if notattext:
        result += "\\hfill \\mbox{\\small \\notescolor{" + notattext + "}}"
    
    # Add newlines at the end
    result += "\n\n"
    
    return result

def week1pagenotes():  # We build a week spread
    latex = ""
    vecka = spliceyear([])
    vecka = purge(vecka)
    for envecka in vecka:
        n = 0
        versoheader = getheader(envecka[0:7])

        for dagar in envecka:
            notattext = notat(dagar)
            is_saturday = (n == 5)  # Check if the day is Saturday
            if n < 7:  # mon -- sun
                if n == 0:
                    latex += "\\Large\\bfseries " + versoheader + " " + " \\hfill \\normalfont\\small " + currweek + " " + getvecka(dagar) + "\n\n"
                    latex += "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                
                # Use the helper function
                latex += format_day(dagar, notattext, is_saturday)

                if n < 6:
                    latex += "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 6:
                    latex += "\\vspace{\stretch{1}}\\pagebreak\n\n"
                    latex += "\\hfill \\small " + notesden + " \n\n"
                    latex += "\\pagebreak\n\n"
            n += 1
    return latex

def week2pages():  # We build a week spread
    latex = ""
    vecka = spliceyear([])
    vecka = purge(vecka)
    for envecka in vecka:
        n = 0
        versoheader = getheader(envecka[0:3])
        rectoheader = getheader(envecka[3:7])

        for dagar in envecka:
            notattext = notat(dagar)
            is_saturday = (n == 5)  # Check if the day is Saturday
            if n < 3:  # måndag -- onsdag
                if n == 0:
                    latex += "\\Large\\bfseries " + versoheader + " " + " \\hfill \\normalfont\\small " + currweek + " " + getvecka(dagar) + "\n\n"
                    latex += "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                    latex += "\\normalsize " + thisweek + "\n\n"
                    latex += "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                
                # Use the helper function
                latex += format_day(dagar, notattext, is_saturday)

                if n < 2:
                    latex += "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 2:
                    latex += "\\vspace{\stretch{1}}\\pagebreak\n\n"
            else:
                if n == 3:
                    latex += "\\hfill \\Large\\bfseries " + rectoheader + " " + " \\normalfont\\normalsize\n\n"
                    latex += "\\vspace{-4.5mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                
                # Use the helper function
                latex += format_day(dagar, notattext, is_saturday)

                if n < 6:
                    latex += "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 6:
                    latex += "\\vspace{\stretch{1}}\\pagebreak\n\n"
            n += 1
    return latex

def week2pageswf():  # We build a week spread
    latex = ""
    vecka = spliceyear([])
    vecka = purge(vecka)
    for envecka in vecka:
        n = 0
        versoheader = getheader(envecka[0:3])
        rectoheader = getheader(envecka[3:7])

        for dagar in envecka:
            notattext = notat(dagar)
            is_saturday = (n == 5)  # Check if the day is Saturday
            if n < 3:  # måndag -- onsdag
                if n == 0:
                    latex += "\\Large\\bfseries " + versoheader + " " + " \\hfill \\normalfont\\small " + currweek + " " + getvecka(dagar) + "\n\n"
                    latex += "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                    latex += "\\normalsize " + thisweek + "\n\n"
                    latex += "\\vspace{\stretch{0.2}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                
                # Use the helper function
                latex += format_day(dagar, notattext, is_saturday)

                if n < 2:
                    latex += "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 2:
                    latex += "\\vspace{\stretch{1}}\\pagebreak\n\n"
            else:
                if n == 3:
                    latex += "\\hfill \\Large\\bfseries " + rectoheader + " " + " \\normalfont\\normalsize\n\n"
                    latex += "\\vspace{-4.5mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                
                # Use the helper function
                latex += format_day(dagar, notattext, is_saturday)

                if n < 5:
                    latex += "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 5:
                    latex += "\\vspace{\stretch{0.6}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 6:
                    latex += "\\vspace{\stretch{0.6}}\\pagebreak\n\n"
            n += 1
    return latex


def weekonepage():  # We build a week spread with a special "gold" layout
    latex = ""
    vecka = spliceyear([])
    vecka = purge(vecka)
    for envecka in vecka:
        n = 0
        versoheader = getheader(envecka[0:7])

        for dagar in envecka:
            notattext = notat(dagar)
            is_saturday = (n == 5)  # Check if the day is Saturday
            if n < 7:  # Monday to Sunday
                if n == 0:
                    latex += "\\Large\\bfseries " + versoheader + " \\hfill \\normalfont\\small " + currweek + " " + getvecka(dagar) + "\n\n"
                    latex += "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                
                # Use the helper function
                latex += format_day(dagar, notattext, is_saturday)

                if n < 6:
                    latex += "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 6:
                    latex += "\\vspace{\stretch{1}}\\pagebreak\n\n"
            n += 1
    return latex

def onedayperpage():  # We build a layout with one day per page
    latex = ""
    vecka = spliceyear([])
    vecka = purge(vecka)
    for envecka in vecka:
        n = 0  # Initialize counter at the beginning of each week
        for dagar in envecka:
            notattext = notat(dagar)
            is_saturday = (n == 5)  # Check if the day is Saturday

            # Header for the day
            latex += "\\Large\\bfseries " + getheadersingle([dagar]) + " \\hfill \\normalfont\\small " + currweek + " " + getvecka(dagar) + "\n\n"
            latex += "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"

            # Use the helper function
            latex += format_day(dagar, notattext, is_saturday)

            # Add a page break after each day
            latex += "\\vspace{\stretch{1}}\\pagebreak\n\n"
            
            n += 1  # Increment the counter for each day
    return latex

    
def preamble(): # This is the preamle
    latex = ""
    latex = latex + "\documentclass[11pt,titlepage]{article}\n"
    if language == "en":
        latex = latex + "\\usepackage[english]{babel}\n"
    else:
        latex = latex + "\\usepackage[swedish]{babel}\n"
    latex = latex + "\\usepackage{fontspec}\n"
    latex = latex + "\\usepackage{graphicx}\n"
    latex = latex + "\\usepackage{parskip}\n"
    latex = latex + "\\usepackage{tikz}\n"
    latex = latex + "\\usepackage{pifont}\n"
    latex = latex + "\\usepackage[bookmarks=true,pdfborder={0 0 0}]{hyperref}\n"
    latex = latex + "\\usepackage[dvips=false,pdftex=false,vtex=false,twoside]{geometry}\n"
    latex = latex + "\\usepackage[cross,a4,center,dvips,noinfo,odd]{crop}\n"
    latex = latex + "\\defaultfontfeatures{Mapping=tex-text}\n"
    latex = latex + "\\setmainfont[BoldFont=Cronos Pro, ItalicFont=Cronos Pro Light Italic, BoldItalicFont=Cronos Pro Semibold, SlantedFont=Cronos Pro Bold, SmallCapsFont =Cronos Pro Light, SmallCapsFeatures={LetterSpace=1.15, Letters=SmallCaps}, Numbers={OldStyle, Proportional}, Scale=0.75 ] {Cronos Pro Light}\n"
    latex = latex + "\geometry{paperwidth=" + paperwidth + "mm, paperheight=" + paperheight + "mm, margin=" + margin + "mm, bottom=" + bottom + "mm, top=" + top + "mm, left=" + left + "mm, nohead}\n\n"
    latex = latex + "\\newcommand*\circled[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=1pt,minimum height=4.5mm,minimum width=4.5mm, line width=0.1pt] (char) {#1};}}\n\n"
    
    if color_mode == "color":
        latex += "\\newcommand*\\circledfill[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=0.1pt,minimum height=4.55mm,minimum width=4.55mm, line width=0.1pt, fill=red!60!black] (char) {#1};}}\n\n"
        # Define a new command for red notes text
        latex += "\\newcommand*\\notescolor[1]{\\textcolor{red!60!black}{#1}}\n\n"
    else:
        latex += "\\newcommand*\\circledfill[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=0.1pt,minimum height=4.55mm,minimum width=4.55mm, line width=0.1pt, fill=black] (char) {#1};}}\n\n"
        # In BW mode, notes are black
        latex += "\\newcommand*\\notescolor[1]{#1}\n\n"
    
    # Make the color_mode variable accessible globally
    global is_color_mode
    is_color_mode = (color_mode == "color")
    
    latex = latex + "\\newcommand{\\tikzcircle}[2]{\\tikz[baseline=-0.5ex]\draw[#2,radius=#1,ultra thin] (0,0) circle ;}\n\n"
    latex = latex + "\\pagenumbering{gobble}\n\n"
    return latex

def opening(): # This is the opening part of the LaTeX document
    latex = ""
    latex = latex + "\\begin{document}\n\n"
    latex = latex + "\\title{\\bfseries\itshape \\Huge " + theyear + " " + str(year) + "\\\ \\vspace{0.25em} \\Large \\normalfont " + titel + "}\n\\author{\\emph{" + av + "} Joakim Hertze}\n\\maketitle\n\n\\pagebreak\n\n"
    return latex
    
def closing(): # This is the closing part of the document
    latex = ""
    latex = latex + "\end{document}\n\n"
    return latex
    
def getmatter(filecontents):  # Reads front or back matter from file
    contents = "\n".join(filecontents)
    return contents
    
# Lets start this already
#
# If the script is called with arguments, it's run without feedback. Otherwise we try
# to create some friendly interaction

if len(sys.argv) < 2: # No arguments are given
    print ("\n\nA L F I E\n\nA somewhat clever diary generator for Filofax-sized binders")
    print ("\n---------------------------------------------------------\n")
    print ("\nHello,")
    print ("\nI have some questions before we begin:\n")

    paper = ""
    layout = ""
    language = ""
    year = ""
    frontmatter = ""
    backmatter = ""
    match = False
    dolatex = ""
    color_mode = ""

    while not (paper == "personal" or paper == "a5" or paper == "a6"or paper == "pocket"): # Make sure a correct format is chosen
        paper_input = input("\n> What format should I use for your insert (pocket/personal/a5/a6)? [personal] ")
        # Use "personal" as default if user just presses Enter
        paper = paper_input if paper_input else "personal"

    while not (color_mode == "color" or color_mode == "bw"): # Make sure the answer is color or bw
        color_mode_input = input("\n> Should I use color or black & white mode (color/bw)? [bw] ").strip().lower()
        # Use "bw" as default if user just presses Enter
        color_mode = color_mode_input if color_mode_input else "bw"
        
    while not (layout == "w2p" or layout == "w1p" or layout == "w2pwf" or layout == "w4p" or layout == "wg" or layout == "1d2p" or layout == "w2pmargins"): # Make sure a correct layout is chosen
        layout_input = input("\n> What layout should I use for your insert (w1p/w2p/w2pwf/w4p/wg/1d2p/w2pmargins)? [w1p] ")
        # Use "w1p" as default if user just presses Enter
        layout = layout_input if layout_input else "w1p"

    while not (language == "sv" or language == "de" or language == "en"): # # Make sure a correct language is chosen
        language_input = input("\n> What language should I use (sv/de/en)? [sv] ")
        # Use "sv" as default if user just presses Enter
        language = language_input if language_input else "sv"
    
    while not match: # # Make sure it's a valid year
        # Get current year for default
        current_year = datetime.datetime.now().year
        year_input = input("\n> What year do you need (YYYY)? [{}] ".format(current_year))
        
        # Use current year if user just presses Enter
        if not year_input:
            year = current_year
            match = True
        else:
            # Otherwise validate the input year
            try:
                year = int(year_input)
                match = re.search("^\d{4}$", str(year))
            except ValueError:
                match = False
                print("Please enter a valid 4-digit year.")
    
    while not (frontmatter == "yes" or frontmatter == "no"): # Make sure the answer is yes or no
        frontmatter_input = input("\n> Shall I include frontmatter (yes/no)? [no] ")
        # Use "no" as default if user just presses Enter
        frontmatter = frontmatter_input if frontmatter_input else "no"
    
    while not (backmatter == "yes" or backmatter == "no"): # Make sure the answer is yes or no
        backmatter_input = input("\n> Shall I include backmatter (yes/no)? [no] ")
        # Use "no" as default if user just presses Enter
        backmatter = backmatter_input if backmatter_input else "no"


else: # Arguments are provided at launch
    match = False
    args = sys.argv[1].split("-")
    
    # Updated argument order - color_mode is now the second parameter
    paper = args[0] if len(args) > 0 else "personal"
    color_mode = args[1] if len(args) > 1 else "bw"  # Default to bw if not specified
    layout = args[2] if len(args) > 2 else "w1p"
    language = args[3] if len(args) > 3 else "en"
    
    # Year needs validation
    try:
        year = int(args[4]) if len(args) > 4 else datetime.datetime.now().year
    except (ValueError, IndexError):
        year = datetime.datetime.now().year
    
    frontmatter = args[5] if len(args) > 5 else "no"
    backmatter = args[6] if len(args) > 6 else "no"
    dolatex = args[7] if len(args) > 7 else "no"

# Set paper dimensions according to provided argument or choice  
  
if paper == "a5":
    paperheight = "212"
    paperwidth = "150"
    margin = "5.5"
    left = "13.5"
    top = "5.5"
    bottom = "10"
elif paper == "a6":
    paperheight = "150"
    paperwidth = "107"
    margin = "4"
    left = "13"
    top = "2"
    bottom = "3.5"
elif paper == "pocket":
    paperheight = "122"
    paperwidth = "83"
    margin = "2"
    left = "12"
    top = "2"
    bottom = "6"
else:
    paperheight = "173"
    paperwidth = "97"
    margin = "3"
    left = "11"
    top = "2"
    bottom = "3.5"
    
# Set proper language according to argument or choice

if language == "en":
    dayname = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    monthname = ["January","February","Mars","April","May","June","July","August","September","October","November","December"]
    thisweek = "this week"
    currweek = "week"
    saturday = "saturday"
    sunday = "sunday"
    av = "by"
    notesden = "notes"
    theyear = "The Year"
    titel = "for " + paper.title() + " Size"
    gratitude = "What have you felt grateful for this week?"
elif language == "de":
    dayname = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
    monthname = ["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
    thisweek = "Diese Woche"
    currweek = "Woche"
    saturday = "Samstag"
    sunday = "Sonntag"
    av = "von"
    notesden = "Notizen"
    theyear = "Das Jahr"
    titel = "für " + paper.title() + " Size"
    gratitude = "Wofür warst Du diese Woche dankbar?"
else:
    dayname = ["måndag","tisdag","onsdag","torsdag","fredag","lördag","söndag"]
    monthname = ["januari","februari","mars","april","maj","juni","juli","augusti","september","oktober","november","december"]
    thisweek = "denna vecka"
    currweek = "vecka"
    saturday = "lördag"
    sunday = "söndag"
    av = "av"
    notesden = "anteckningar"
    theyear = "Året"
    titel = "för " + paper.title()
    gratitude = "Vad har du känt tacksamhet över denna vecka?"

# Read supplementary files

holidays = readfile("holidays-" + str(year) + "-" + language + ".txt")
if holidays != False and len(sys.argv) < 2:
    print ("\n--> I've successfully loaded *holidays-" + str(year) + "-" + language + ".txt*.")

notes = readfile("notes-" + str(year) + "-" + language +  ".txt")
if notes != False and len(sys.argv) < 2:
    print ("\n--> I've successfully loaded *notes-" + str(year) + "-" + language +  ".txt*.")

weeknotes = readfile("weeknotes-" + str(year) + "-" + language +  ".txt")
if weeknotes != False and len(sys.argv) < 2:
    print ("\n--> I've successfully loaded *weeknotes-" + str(year) + "-" + language +  ".txt*.")

# Let's assemble the diary

latex = ""
latex = preamble() + opening()

if frontmatter == "yes":
    filefrontmatter = readfile("frontmatter-" + str(year) + "-" + language + ".txt")
    if filefrontmatter != False:
        latex = latex + getmatter(filefrontmatter) + "\\pagebreak\n\n"

if layout == "w2p":
    latex = latex + week2pages()
elif layout == "w2pwf":
    latex = latex + week2pageswf()
elif layout == "w1pnotes":
    latex = latex + week1pagenotes()
elif layout == "1dp":
    latex = latex + onedayperpage()
else:
    latex = latex + weekonepage()

if backmatter == "yes":
    filebackmatter = readfile("backmatter-" + str(year) + "-" + language + ".txt")
    if filebackmatter != False:
        latex = latex + "\\pagebreak\n\n" + getmatter(filebackmatter)
        
latex = latex + closing()

if len(sys.argv) < 2: # Only feedback is script is run without arguments
    print ("\nI'm building your calendar now.")
    print ("\nDone!")

# Write it to file

f = open("diary-" + paper + "-" + str(year) + "-" + language + ".tex", "w")
f.write(latex)

if len(sys.argv) < 2: # Only feedback is script is run without arguments
    print ("\nI've written the LaTeX document to *diary-" + paper + "-" + str(year) + "-" + language + ".tex*.")

if len(sys.argv) < 2:    
    while not (dolatex == "yes" or dolatex == "no"): # Make sure the answer is yes or no
        dolatex_input = input("\n> Shall try to typeset your LaTeX document (yes/no)? [yes] ")
        # Use "yes" as default if user just presses Enter
        dolatex = dolatex_input if dolatex_input else "yes"

if dolatex == "yes": # Shall it try to typeset the LaTeX file?
    os.system("xelatex diary-" + paper + "-" + str(year) + "-" + language + ".tex")
    print ("\nYour file has been typeset.")
    os.system("open diary-" + paper + "-" + str(year) + "-" + language + ".pdf")
    
if len(sys.argv) < 2: # Signing out
    print ("\n\nAll done!")    
    print ("\n\n---------------------------------------------------------\n\n")