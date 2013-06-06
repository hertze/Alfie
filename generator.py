#! /usr/bin/env python3.3

import calendar
import datetime

dayname = ["måndag","tisdag","onsdag","torsdag","fredag","lördag","söndag"]
monthname = ["januari","februari","mars","april","maj","juni","juli","augusti","september","oktober","november","december"]

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
        month = month + " / " + month2
    return str(month)


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
            if n < 3: # måndag -- onsdag
                if n == 0:
                    latex = latex + "\\Large\\ttfamily " + versomonth + " \\hfill \\normalfont\\small vecka " + getvecka(dagar) + "\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.5pt}\n\n"
                    latex = latex + "\\normalsize Denna vecka\n\n"
                    latex = latex + "\\vspace{25mm}\\rule{\\textwidth}{0.1pt}\n\n"
                latex = latex + "\\large\\ttfamily \\circled{" + str(dagar[2]) + "} \\hspace{0.2mm} \\normalfont\\normalsize " + str(dagar[3]) + "\n\n"    
                if n < 2:
                    latex = latex + "\\vspace{25mm}\\rule{\\textwidth}{0.1pt}\n\n"
                if n == 2:
                    latex = latex + "\\pagebreak\n\n"            
            else:
                if n == 3:
                    latex = latex + "\\hfill \\Large\\ttfamily " + rectomonth + " \\normalfont\\normalsize\n\n"
                    latex = latex + "\\vspace{-4mm}\\rule{\\textwidth}{0.5pt}\n\n"
                if str(dagar[3]) == "lördag" or str(dagar[3]) == "söndag":
                    latex = latex + "\\hfill " + str(dagar[3]) + " \\hspace{0.2mm} \\large \\ttfamily \\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} \\normalfont\\normalsize\n\n"
                else:
                    latex = latex + "\\hfill " + str(dagar[3]) + " \\hspace{0.2mm} \\large \\ttfamily \\circled{" + str(dagar[2]) + "} \\normalfont\\normalsize\n\n"
                if n < 6:
                    latex = latex + "\\vspace{25mm}\\rule{\\textwidth}{0.1pt}\n\n"
                if n == 6:
                    latex = latex + "\\pagebreak\n\n"  
            n = n + 1
    return latex
    

def preamble():
    latex = ""
    latex = latex + "\documentclass[11pt,titlepage]{article}\n"
    latex = latex + "\\usepackage[swedish]{babel}\n"
    latex = latex + "\\usepackage{fontspec}\n\\usepackage{graphicx}\n\\usepackage{parskip}\n\\usepackage{tikz} \\usepackage[dvips=false,pdftex=false,vtex=false,twoside]{geometry}\n\\usepackage[cross,a4,center,dvips,noinfo,odd]{crop}\n\defaultfontfeatures{Mapping=tex-text}\n\setromanfont[Ligatures={Common}, Numbers={OldStyle}, Scale=0.7]{Source Sans Pro Light}\n\setmonofont[Ligatures={Common}, Numbers={OldStyle}, Scale=0.7]{Source Sans Pro}\n\n"
    latex = latex + "\geometry{paperwidth=95mm, paperheight=171mm, margin=5mm, bottom=0mm, top=3mm, left=9mm, nohead}\n\n"
    latex = latex + "\\newcommand*\circled[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=1pt,minimum height=5mm,minimum width=5mm, line width=0.1pt] (char) {#1};}}\n\n"
    latex = latex + "\\newcommand*\circledfill[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=0.1pt,minimum height=5mm,minimum width=5mm, , line width=0.1pt, fill=black] (char) {#1};}}\n\n"
    latex = latex + "\linespread{1.2}\n\n"
    return latex

def opening():
    latex = ""
    latex = latex + "\\begin{document}\n\n"
    latex = latex + "\\title{Kalender för " + str(year) + "}\n\\author{\\emph{av} Joakim Hertze}\n\\maketitle\n\n\\pagebreak\n\n"
    return latex
    
def closing():
    latex = ""
    latex = latex + "\end{document}\n\n"
    return latex

year = int(input("Villket år? "))

# Nu sätter vi samman allt #

latex = ""
latex = preamble() + opening() + buildspreads() + closing()

print (latex)
    

# Skriver till fil #

f = open("kalender.tex", "w")
f.write(latex)

print ("Skrivet!")