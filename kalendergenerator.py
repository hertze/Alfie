#! /usr/bin/env python3.3

import calendar
import datetime

language = input("What language (sv/en)? ")
year = int(input("What year (YYYY)? "))

if language == "en":
    dayname = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    monthname = ["January","February","Mars","April","May","June","July","August","September","October","November","December"]
    thisweek = "this week"
    currweek = "week"
    av = "by"
    titel = "in Filofax Personal Size"
else:
    dayname = ["måndag","tisdag","onsdag","torsdag","fredag","lördag","söndag"]
    monthname = ["januari","februari","mars","april","maj","juni","juli","augusti","september","oktober","november","december"]
    thisweek = "denna vecka"
    currweek = "vecka"
    av = "av"
    titel = "för Filofax Personal"

# Funktioner #

def spliceyear(vecka):
    c = calendar.LocaleTextCalendar(locale='sv_SE')
    for wholeyear in c.yeardatescalendar(year, 1): # Spalta upp hela året
        
        for months in wholeyear:
            for weeks in months:
                dennavecka = []
                # Här kommer en vecka i taget #
                for days in weeks:
                    d = datetime.date
                    dt = d.timetuple(days)
                    weeknumber = d.isocalendar(days)
                
                    month = monthname[dt[1]-1]
                    datum = dt[2]
                    weekday = dayname[dt[6]]
                    veckonummer = weeknumber[1]
                
                    dennavecka.append([month, veckonummer, datum, weekday])
                vecka.append(dennavecka)
    return vecka
    
def purge(vecka):
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

def getvecka(dagar):
    vecka = dagar[1]
    return str(vecka)
    
def getmonth(envecka):
    month = envecka[0][0]
    month2 = envecka[-1][0]
    if month != month2:
        month = month + "--" + month2
    return str(month)
    
def holiday(dagar):
    if str(dagar[3]) == "lördag" or str(dagar[3]) == "söndag":
        return True
    else:
        idag = str(dagar[2]) + " " + str(dagar[0])
        f = open("holiday-" + str(year) + ".txt", "r")
        for line in f:
            if idag == line.rstrip():
                return True
                
def notat(dagar):
    notat = ""
    idag = str(dagar[2]) + " " + str(dagar[0])
    f = open("notat-" + str(year) + ".txt", "r")
    for line in f:
        line = line.split(": ")
        if idag == line[0]:
            notat = line[1]
    return notat  

def buildspreads():
    latex = ""
    vecka = []
    vecka = spliceyear(vecka)
    vecka = purge(vecka)
    for envecka in vecka:
        n = 0
        versomonth = getmonth(envecka[0:2])
        rectomonth = getmonth(envecka[3:6])
        
        for dagar in envecka:
            notattext = notat(dagar)
            if n < 3: # måndag -- onsdag
                if n == 0:
                    latex = latex + "\\Large\\ttfamily " + versomonth + " " + str(year) + " \\hfill \\normalfont\\small " + currweek + " " + getvecka(dagar) + "\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.5pt}\\vspace{-2mm}\n\n"
                    latex = latex + "\\normalsize " + thisweek + "\n\n"
                    latex = latex + "\\vspace{28.5mm}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if notattext != "":
                    latex = latex + "\\large\\ttfamily \\circled{" + str(dagar[2]) + "} \\hspace{0.2mm} \\normalfont\\normalsize " + str(dagar[3]) + "\\hfill \\mbox{\\small " +  str(notattext) + "}\n\n"
                else:
                    latex = latex + "\\large\\ttfamily \\circled{" + str(dagar[2]) + "} \\hspace{0.2mm} \\normalfont\\normalsize " + str(dagar[3]) + "\n\n"
                
                if n < 2:
                    latex = latex + "\\vspace{28.5mm}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 2:
                    latex = latex + "\\pagebreak\n\n"            
            else:
                if n == 3:
                    latex = latex + "\\hfill \\Large\\ttfamily " + rectomonth + " " + str(year) + " \\normalfont\\normalsize\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.5pt}\\vspace{-2mm}\n\n"
                if holiday(dagar):
                    if notattext != "":
                        latex = latex + "\\mbox{\\small " + str(notattext) + "} \\hfill " + str(dagar[3]) + " \\hspace{0.2mm} \\large \\ttfamily \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\normalfont\\normalsize\n\n"
                    else:
                        latex = latex + "\\hfill " + str(dagar[3]) + " \\hspace{0.2mm} \\large \\ttfamily \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\normalfont\\normalsize\n\n"
                else:
                    if notattext != "":
                        latex = latex + str(notattext) + "\\hfill " + str(dagar[3]) + " \\hspace{0.2mm} \\large \\ttfamily \\circled{" + str(dagar[2]) + "} \\normalfont\\normalsize\n\n"
                    else:
                        latex = latex + "\\hfill " + str(dagar[3]) + " \\hspace{0.2mm} \\large \\ttfamily \\circled{" + str(dagar[2]) + "} \\normalfont\\normalsize\n\n"
                if n < 6:
                    latex = latex + "\\vspace{28.5mm}\\rule{\\textwidth}{0.1pt}\\vspace{-2mm}\n\n"
                if n == 6:
                    latex = latex + "\\pagebreak\n\n"  
            n = n + 1
    return latex
    
def preamble():
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
    latex = latex + "\\usepackage[dvips=false,pdftex=false,vtex=false,twoside]{geometry}\n"
    latex = latex + "\\usepackage[cross,a4,center,dvips,noinfo,odd]{crop}\n"
    latex = latex + "\\defaultfontfeatures{Mapping=tex-text}\n"
    latex = latex + "\\setromanfont[Ligatures={Common}, Numbers={OldStyle}, Scale=0.7]{Source Sans Pro Light}\n"
    latex = latex + "\\setmonofont[Ligatures={Common}, Numbers={OldStyle}, Scale=0.7]{Source Sans Pro}\n\n"
    latex = latex + "\\setsansfont[Ligatures={Common}, Numbers={OldStyle}, Scale=2.81]{Adobe Jenson Pro Light}\n\n"
    latex = latex + "\geometry{paperwidth=95mm, paperheight=171mm, margin=5mm, bottom=0mm, top=3mm, left=11mm, nohead}\n\n"
    latex = latex + "\\newcommand*\circled[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=1pt,minimum height=4mm,minimum width=4mm, line width=0.1pt] (char) {#1};}}\n\n"
    latex = latex + "\\newcommand*\circledfill[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=0.1pt,minimum height=4.5mm,minimum width=4.5mm, , line width=0.1pt, fill=black] (char) {#1};}}\n\n"
    return latex

def opening():
    latex = ""
    latex = latex + "\\begin{document}\n\n"
    latex = latex + "\\title{\\sffamily " + str(year) + "\\\ \\vspace{0.25em} \\normalfont " + titel + "}\n\\author{\\emph{" + av + "} Joakim Hertze}\n\\maketitle\n\n\\pagebreak\n\n"
    return latex
    
def closing():
    latex = ""
    latex = latex + "\end{document}\n\n"
    return latex

# Nu sätter vi samman allt #

latex = ""
latex = preamble() + opening() + buildspreads() + closing()
    

# Skriver till fil #

f = open("kalender.tex", "w")
f.write(latex)

print ("Skrivet till *kalender.tex*!")