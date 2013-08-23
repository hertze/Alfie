#! /usr/bin/env python3.3
# -*- coding: utf-8 -*-

# A L F I E
# version 1.4
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
    
def holiday(dagar): # Are this day a holiday?
    if str(dagar[3]) == saturday or str(dagar[3]) == sunday:
        return True
    else:
        idag = str(dagar[2]) + " " + str(dagar[0])
        if holidays != False:
            for line in holidays:
                if idag == line.rstrip():
                    return True
                
def notat(dagar): # Checks if there is a note for the current day
    notat = ""
    idag = str(dagar[2]) + " " + str(dagar[0])
    if notes != False:
        for line in notes:
            line = line.split(": ")
            if idag == line[0]:
                notat = line[1]
    return notat  

def week2pages(): # We build a week spread
    latex = ""
    vecka = []
    vecka = spliceyear(vecka)
    vecka = purge(vecka)
    for envecka in vecka:
        n = 0
        versoheader = getheader(envecka[0:3])
        rectoheader = getheader(envecka[3:7])
        
        for dagar in envecka:
            notattext = notat(dagar)
            if n < 3: # måndag -- onsdag
                if n == 0:
                    latex = latex + "\\Large\\bfseries " + versoheader + " " + " \\hfill \\normalfont\\small " + currweek + " " + getvecka(dagar) + "\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                    latex = latex + "\\normalsize " + thisweek + "\n\n"
                    latex = latex + "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if holiday(dagar):
                    if notattext != "":
                        latex = latex + "\\large\\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\\hfill \\mbox{\\small\\itshape " +  str(notattext) + "}\n\n"
                    else:
                        latex = latex + "\\large\\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\n\n"
                else:
                    if notattext != "":
                        latex = latex + "\\large\\bfseries \\circled{" + str(dagar[2]) + "} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\\hfill \\mbox{\\small\\itshape " +  str(notattext) + "}\n\n"
                    else:
                        latex = latex + "\\large\\bfseries \\circled{" + str(dagar[2]) + "} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\n\n"
                
                if n < 2:
                    latex = latex + "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 2:
                    latex = latex + "\\vspace{\stretch{1}}\\pagebreak\n\n"            
            else:
                if n == 3:
                    latex = latex + "\\hfill \\Large\\bfseries " + rectoheader + " " + " \\normalfont\\normalsize\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                if holiday(dagar):
                    if notattext != "":
                        latex = latex + "\\mbox{\\small\\itshape " + str(notattext) + "} \\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\normalfont\\normalsize\n\n"
                    else:
                        latex = latex + "\\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\normalfont\\normalsize\n\n"
                else:
                    if notattext != "":
                        latex = latex + "\\mbox{\\small\\itshape " + str(notattext) + "} \\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries \\circled{" + str(dagar[2]) + "} \\normalfont\\normalsize\n\n"
                    else:
                        latex = latex + "\\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries \\circled{" + str(dagar[2]) + "} \\normalfont\\normalsize\n\n"
                if n < 6:
                    latex = latex + "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 6:
                    latex = latex + "\\vspace{\stretch{1}}\\pagebreak\n\n"  
            n = n + 1
    return latex
    
def week2pageswf2(): # We build a week spread
    latex = ""
    vecka = []
    vecka = spliceyear(vecka)
    vecka = purge(vecka)
    for envecka in vecka:
        n = 0
        versoheader = getheader(envecka[0:3])
        rectoheader = getheader(envecka[3:7])
        
        for dagar in envecka:
            notattext = notat(dagar)
            if n < 3: # måndag -- onsdag
                if n == 0:
                    latex = latex + "\\Large\\bfseries " + versoheader + " " + " \\hfill \\normalfont\\small " + currweek + " " + getvecka(dagar) + "\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                    latex = latex + "\\normalsize " + thisweek + "\n\n"
                    latex = latex + "\\vspace{\stretch{0.2}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if holiday(dagar):
                    if notattext != "":
                        latex = latex + "\\large\\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\\hfill \\mbox{\\small\\itshape " +  str(notattext) + "}\n\n"
                    else:
                        latex = latex + "\\large\\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\n\n"
                else:
                    if notattext != "":
                        latex = latex + "\\large\\bfseries \\circled{" + str(dagar[2]) + "} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\\hfill \\mbox{\\small\\itshape " +  str(notattext) + "}\n\n"
                    else:
                        latex = latex + "\\large\\bfseries \\circled{" + str(dagar[2]) + "} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\n\n"
                
                if n < 2:
                    latex = latex + "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 2:
                    latex = latex + "\\vspace{\stretch{1}}\\pagebreak\n\n"            
            else:
                if n == 3:
                    latex = latex + "\\hfill \\Large\\bfseries " + rectoheader + " " + " \\normalfont\\normalsize\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                if holiday(dagar):
                    if notattext != "":
                        latex = latex + "\\mbox{\\small\\itshape " + str(notattext) + "} \\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\normalfont\\normalsize\n\n"
                    else:
                        latex = latex + "\\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\normalfont\\normalsize\n\n"
                else:
                    if notattext != "":
                        latex = latex + "\\mbox{\\small\\itshape " + str(notattext) + "} \\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries\\itshape \\circled{" + str(dagar[2]) + "} \\normalfont\\normalsize\n\n"
                    else:
                        latex = latex + "\\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries \\circled{" + str(dagar[2]) + "} \\normalfont\\normalsize\n\n"
                if n < 5:
                    latex = latex + "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 5:
                    latex = latex + "\\vspace{\stretch{0.6}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 6:
                    latex = latex + "\\vspace{\stretch{0.6}}\\pagebreak\n\n"  
            n = n + 1
    return latex
    
def week2pageswf(): # We build a week spread
    latex = ""
    vecka = []
    vecka = spliceyear(vecka)
    vecka = purge(vecka)
    for envecka in vecka:
        n = 0
        versoheader = getheader(envecka[0:3])
        rectoheader = getheader(envecka[3:7])
        
        for dagar in envecka:
            notattext = notat(dagar)
            if n < 3: # måndag -- onsdag
                if n == 0:
                    latex = latex + "\\Large\\bfseries " + versoheader + " " + " \\hfill \\normalfont\\small " + currweek + " " + getvecka(dagar) + "\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                if holiday(dagar):
                    if notattext != "":
                        latex = latex + "\\large\\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\\hfill \\mbox{\\small\\itshape " +  str(notattext) + "}\n\n"
                    else:
                        latex = latex + "\\large\\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\n\n"
                else:
                    if notattext != "":
                        latex = latex + "\\large\\bfseries \\circled{" + str(dagar[2]) + "} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\\hfill \\mbox{\\small\\itshape " +  str(notattext) + "}\n\n"
                    else:
                        latex = latex + "\\large\\bfseries \\circled{" + str(dagar[2]) + "} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\n\n"
                
                if n < 2:
                    latex = latex + "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 2:
                    latex = latex + "\\vspace{\stretch{1}}\\pagebreak\n\n"            
            else:
                if n == 3:
                    latex = latex + "\\hfill \\Large\\bfseries " + rectoheader + " " + " \\normalfont\\normalsize\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                if holiday(dagar):
                    if notattext != "":
                        latex = latex + "\\mbox{\\small\\itshape " + str(notattext) + "} \\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\normalfont\\normalsize\n\n"
                    else:
                        latex = latex + "\\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\normalfont\\normalsize\n\n"
                else:
                    if notattext != "":
                        latex = latex + "\\mbox{\\small\\itshape " + str(notattext) + "} \\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries \\circled{" + str(dagar[2]) + "} \\normalfont\\normalsize\n\n"
                    else:
                        latex = latex + "\\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries \\circled{" + str(dagar[2]) + "} \\normalfont\\normalsize\n\n"
                if n < 5:
                    latex = latex + "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 5:
                    latex = latex + "\\vspace{\stretch{0.5}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 6:
                    latex = latex + "\\vspace{\stretch{0.5}}\\pagebreak\n\n"  
            n = n + 1
    return latex
    
def week2pageswnotes(): # We build a week spread
    latex = ""
    vecka = []
    vecka = spliceyear(vecka)
    vecka = purge(vecka)
    for envecka in vecka:
        n = 0
        versoheader = getheader(envecka[0:5])
        rectoheader = getheader(envecka[5:7])
        
        for dagar in envecka:
            notattext = notat(dagar)
            if n < 5: # mon -- fri
                if n == 0:
                    latex = latex + "\\Large\\bfseries " + versoheader + " " + " \\hfill \\normalfont\\small " + currweek + " " + getvecka(dagar) + "\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                if holiday(dagar):
                    if notattext != "":
                        latex = latex + "\\large\\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\\hfill \\mbox{\\small\\itshape " +  str(notattext) + "}\n\n"
                    else:
                        latex = latex + "\\large\\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\n\n"
                else:
                    if notattext != "":
                        latex = latex + "\\large\\bfseries \\circled{" + str(dagar[2]) + "} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\\hfill \\mbox{\\small\\itshape " +  str(notattext) + "}\n\n"
                    else:
                        latex = latex + "\\large\\bfseries \\circled{" + str(dagar[2]) + "} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\n\n"
                
                if n < 4:
                    latex = latex + "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 4:
                    latex = latex + "\\vspace{\stretch{1}}\\pagebreak\n\n"            
            else:
                if n == 5:
                    latex = latex + "\\hfill \\Large\\bfseries " + rectoheader + " " + " \\normalfont\\normalsize\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                if holiday(dagar):
                    if notattext != "":
                        latex = latex + "\\mbox{\\small\\itshape " + str(notattext) + "} \\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\normalfont\\normalsize\n\n"
                    else:
                        latex = latex + "\\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\normalfont\\normalsize\n\n"
                else:
                    if notattext != "":
                        latex = latex + "\\mbox{\\small\\itshape " + str(notattext) + "} \\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries \\circled{" + str(dagar[2]) + "} \\normalfont\\normalsize\n\n"
                    else:
                        latex = latex + "\\hfill " + str(dagar[3]) + " \\hspace{0mm} \\large \\bfseries \\circled{" + str(dagar[2]) + "} \\normalfont\\normalsize\n\n"
                if n < 6:
                    latex = latex + "\\vspace{0.2pt}\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 6:
                    latex = latex + "\\vspace{0.2pt}\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                    latex = latex + "\\hfill \\small " + notesden + " \n\n\\vspace{\stretch{4}}\\pagebreak\n\n" 
                    latex = latex + "\\pagebreak\n\n"
            n = n + 1
    return latex
    
def week1page(): # We build a week spread
    latex = ""
    vecka = []
    vecka = spliceyear(vecka)
    vecka = purge(vecka)
    for envecka in vecka:
        n = 0
        versoheader = getheader(envecka[0:7])
        
        for dagar in envecka:
            notattext = notat(dagar)
            if n < 7: # mon -- sun
                if n == 0:
                    latex = latex + "\\Large\\bfseries " + versoheader + " " + " \\hfill \\normalfont\\small " + currweek + " " + getvecka(dagar) + "\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n"
                if holiday(dagar):
                    if notattext != "":
                        latex = latex + "\\large\\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\\hfill \\mbox{\\small\\itshape " +  str(notattext) + "}\n\n"
                    else:
                        latex = latex + "\\large\\bfseries\\itshape \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\n\n"
                else:
                    if notattext != "":
                        latex = latex + "\\large\\bfseries \\circled{" + str(dagar[2]) + "} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\\hfill \\mbox{\\small\\itshape " +  str(notattext) + "}\n\n"
                    else:
                        latex = latex + "\\large\\bfseries \\circled{" + str(dagar[2]) + "} \\hspace{0mm} \\normalfont\\normalsize " + str(dagar[3]) + "\n\n"
                
                if n < 6:
                    latex = latex + "\\vspace{\stretch{1}}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 6:
                    latex = latex + "\\vspace{\stretch{1}}\\pagebreak\n\n" 
                    latex = latex + "\\hfill \\small " + notesden + " \n\n"
                    latex = latex + "\\pagebreak\n\n"          
            n = n + 1
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
    latex = latex + "\\usepackage[bookmarks=true,pdfborder={0 0 0}]{hyperref}\n"
    latex = latex + "\\usepackage[dvips=false,pdftex=false,vtex=false,twoside]{geometry}\n"
    latex = latex + "\\usepackage[cross,a4,center,dvips,noinfo,landscape,odd]{crop}\n"
    latex = latex + "\\defaultfontfeatures{Mapping=tex-text}\n"
    latex = latex + "\\setmainfont[BoldFont=Cronos Pro, ItalicFont=Cronos Pro Light Italic, BoldItalicFont=Cronos Pro Semibold, SmallCapsFont =Cronos Pro Light, SmallCapsFeatures={LetterSpace=1.15, Letters=SmallCaps}, Numbers={OldStyle, Proportional}, Scale=0.75 ] {Cronos Pro Light}\n"
    latex = latex + "\geometry{paperwidth=" + paperwidth + "mm, paperheight=" + paperheight + "mm, margin=" + margin + "mm, bottom=" + bottom + "mm, top=" + top + "mm, left=" + left + "mm, nohead}\n\n"
    latex = latex + "\\newcommand*\circled[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=1pt,minimum height=4.5mm,minimum width=4.5mm, line width=0.1pt] (char) {#1};}}\n\n"
    latex = latex + "\\newcommand*\circledfill[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=0.1pt,minimum height=4.55mm,minimum width=4.55mm, , line width=0.1pt, fill=black] (char) {#1};}}\n\n"
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

    while not (paper == "personal" or paper == "a5" or paper == "pocket"): # # Make sure a correct format is chosen
        paper = input("\n> What format should I use for your insert (pocket/personal/a5)? ")
        
    while not (layout == "w2p" or layout == "w2pn" or layout == "w1p" or layout == "w2pwf" or layout == "w2pwf2"): # # Make sure a correct layout is chosen
        layout = input("\n> What layout should I use for your insert (w1p/w2p/w2pn/w2pwf/w2pwf2)? ")

    while not (language == "sv" or language == "en"): # # Make sure a correct language is chosen
        language = input("\n> What language should I use (sv/en)? ")
    
    while not match: # # Make sure it's a valid yesr
        year = int(input("\n> What year do you need (YYYY)? "))
        match = re.search("^\d{4}$", str(year))
    
    while not (frontmatter == "yes" or frontmatter == "no"): # Make sure the answer is yes or no
        frontmatter = input("\n> Shall I include frontmatter (yes/no)? ")
    
    while not (backmatter == "yes" or backmatter == "no"): # Make sure the answer is yes or no
        backmatter = input("\n> Shall I include backmatter (yes/no)? ")    
else: # Arguments are provided at launch
    match = False
    args = sys.argv[1].split("-")
    paper = args[0]
    layout = args[1]
    language = args[2]
    year = int(args[3])
    frontmatter = args[4]
    backmatter = args[5]
    dolatex = args[6]

# Set paper dimensions according to provided argument or choice  
  
if paper == "a5":
    paperheight = "212"
    paperwidth = "150"
    margin = "5.5"
    left = "12.5"
    top = "5.5"
    bottom = "10"
elif paper == "pocket":
    paperheight = "122"
    paperwidth = "83"
    margin = "4"
    left = "9.5"
    top = "3"
    bottom = "4"
else:
    paperheight = "173"
    paperwidth = "97"
    margin = "3"
    left = "11"
    top = "2"
    bottom = "6"
    
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
    titel = "for Filofax " + paper.title() + " Size"
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
    titel = "för Filofax " + paper.title()

# Read supplementary files

holidays = readfile("holidays-" + str(year) + "-" + language + ".txt")
if holidays != False and len(sys.argv) < 2:
    print ("\n--> I've successfully loaded *holidays-" + str(year) + "-" + language + ".txt*.")

notes = readfile("notes-" + str(year) + "-" + language +  ".txt")
if holidays != False  and len(sys.argv) < 2:
    print ("\n--> I've successfully loaded *notes-" + str(year) + "-" + language +  ".txt*.")

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
elif layout == "w2pwf2":
    latex = latex + week2pageswf2()
elif layout == "w2pn":
    latex = latex + week2pageswnotes()
else:
    latex = latex + week1page()

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
        dolatex = input("\n> Shall try to typeset your LaTeX document (yes/no)? ")

if dolatex == "yes": # Shall it try to typeset the LaTeX file?
    os.system("xelatex diary-" + paper + "-" + str(year) + "-" + language + ".tex")
    print ("\nYour file has been typeset.")
    os.system("open diary-" + paper + "-" + str(year) + "-" + language + ".pdf")
    
if len(sys.argv) < 2: # Signing out
    print ("\n\nHave a nice day!")    
    print ("\n\n---------------------------------------------------------\n\n")