#! /usr/bin/env python3.10
# -*- coding: utf-8 -*-

# A L F I E
# version 2.1
#
# by Joakim Hertze

import calendar
import datetime
import re
import sys
import os

# Initialize global variables with default values
# These will be properly set later based on user input/arguments
year = None
language = "sv"  # Default language
color_mode = "bw"  # Default color mode
dayname = []
monthname = []
thisweek = ""
currweek = ""
saturday = ""
sunday = ""
av = ""
notesden = ""
theyear = ""
titel = ""
gratitude = ""
holidays = []
notes = []
weeknotes = []
paperwidth = "97"  # Default personal size
paperheight = "173"
margin = "3"
left = "11"
top = "2"
bottom = "3.5"
is_color_mode = False


def readfile(name):  # Reads a file and makes it into a list line by line
    try:
        with open(name, "r") as f:  # Use 'with' to ensure the file is properly closed
            return [line.strip() for line in f]  # Use list comprehension for simplicity
    except FileNotFoundError:  # Catch specific exception for missing files
        if len(sys.argv) < 2:  # Only provide feedback if the script is run without arguments
            print(f"\n--> I cannot load {name}, but I'll probably manage without it.")
        return []  # Return empty list instead of False for consistency
    except Exception as e:  # Catch other exceptions and provide feedback
        print(f"\n--> An error occurred while loading {name}: {e}")
        return []  # Return empty list

def spliceyear(vecka):  # Chunk up the year
    c = calendar.LocaleTextCalendar(locale='sv_SE')
    for wholeyear in c.yeardatescalendar(year, 1):  # Iterate over the entire year
        for months in wholeyear:
            for weeks in months:
                dennavecka = []
                for day in weeks:
                    if day.month != 0:  # Skip padding days (outside the current month)
                        weeknumber = day.isocalendar()[1]  # Get ISO week number
                        curryear = day.year
                        month = monthname[day.month - 1]
                        datum = day.day
                        weekday = dayname[day.weekday()]
                        dennavecka.append([month, weeknumber, datum, weekday, curryear])
                if dennavecka:  # Only append non-empty weeks
                    vecka.append(dennavecka)
    return vecka
    
def purge(vecka):  # Remove duplicate weeks
    """
    Removes duplicate weeks from the list by comparing week numbers.
    """
    purged = []
    for i, current_week in enumerate(vecka):
        if i == 0 or current_week[0][1] != vecka[i - 1][0][1]:
            purged.append(current_week)
    return purged

def getvecka(dagar):  # Gets the current week and converts it to a string
    return str(dagar[1])
    
def getheader(envecka):  # Builds the date header for each page
    # Extract month and year from the first and last days of the week
    month_start, year_start = envecka[0][0], str(envecka[0][4])
    month_end, year_end = envecka[-1][0], str(envecka[-1][4])

    # Build the header based on whether the month or year changes within the week
    if month_start != month_end:
        if year_start != year_end:
            header = f"{month_start} {year_start}--{month_end} {year_end}"
        else:
            header = f"{month_start}--{month_end} {year_start}"
    else:
        header = f"{month_start} {year_start}"

    return header
    
    
def getheadersingle(envecka):  # Builds the date header for a single page
    """
    Builds a date header for a single page based on the first day of the week.

    Args:
        envecka (list): A list of days in the week, where each day is represented as a list
                        containing [month, week number, day, weekday, year].

    Returns:
        str: A formatted string representing the month and year of the first day.
    """
    month = envecka[0][0]  # Extract the month from the first day
    year = str(envecka[0][4])  # Extract the year from the first day
    return f"{month} {year}"
    
def holiday(dagar):  # Checks if the given day is a holiday
    """
    Determines if a given day is a holiday.

    Args:
        dagar (list): A list representing a day, where the fourth element is the weekday
                      and the second and first elements represent the day and month.

    Returns:
        bool: True if the day is a holiday, False otherwise.
    """
    # Check if the day is Sunday
    if str(dagar[3]) == sunday:
        return True

    # Check if the day is in the holidays list
    idag = f"{dagar[2]} {dagar[0]}"  # Format: "day month"
    if holidays:
        return any(idag == line.rstrip() for line in holidays)

    return False  # Saturday is no longer treated as a holiday
                
def notat(dagar):  # Checks if there is a note for the current day
    """
    Retrieves a note for the given day, if available.

    Args:
        dagar (list): A list representing a day, where the second and first elements
                      represent the day and month.

    Returns:
        str: The note for the day, or an empty string if no note is found.
    """
    idag = f"{dagar[2]} {dagar[0]}"  # Format: "day month"
    if notes:
        for line in notes:
            date, *note = line.split(": ", 1)  # Split into date and note
            if idag == date:
                return note[0] if note else ""
    return ""
    
def weeknotat(dennavecka):  # Checks if there is a note for the current week
    """
    Retrieves a note for the given week, if available.

    Args:
        dennavecka (str): The identifier for the current week (e.g., "Week 1").

    Returns:
        str: The note for the week, or an empty string if no note is found.
    """
    if not weeknotes:  # Check if weeknotes is empty or False
        return ""

    for line in weeknotes:
        week, *note = line.split(": ", 1)  # Split into week identifier and note
        if dennavecka == week:
            return note[0] if note else ""  # Return the note if it exists

    return ""  # Return an empty string if no match is found
    
def format_day(dagar, notattext, is_saturday=False, is_recto=False):
    """
    Formats a single day's LaTeX representation.

    Args:
        dagar (list): A list representing a day, where the second and first elements
                      represent the day and month.
        notattext (str): The note for the day, if any.
        is_saturday (bool): Whether the day is Saturday.
        is_recto (bool): Whether the page is a recto (right-hand) page.

    Returns:
        str: The LaTeX representation of the day.
    """
    # Start building the LaTeX string
    result = "\\large\\bfseries "
    
    # Add the appropriate circle formatting based on day type
    if is_saturday:  # Saturday (always black circle)
        day_number = "\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=0.1pt,minimum height=4.55mm,minimum width=4.55mm, line width=0.1pt, fill=black] (char) {\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}};}  "
    elif holiday(dagar):  # Holiday or Sunday
        day_number = "\\circledfill{\\bfseries\\textcolor{white}{" + str(dagar[2]) + "}} "
        result = result.replace("\\large\\bfseries", "\\large\\bfseries\\itshape")
    else:  # Regular weekday
        day_number = "\\circled{" + str(dagar[2]) + "} "
    
    # Add the day name
    day_name = "\\normalfont\\normalsize " + str(dagar[3])
    
    # Adjust alignment based on page type
    if is_recto:
        if notattext:
            # On recto pages with notes, put notes to the left
            result = "\\small \\notescolor{" + notattext + "} \\hfill " + day_name + " \\hspace{0mm} " + day_number
        else:
            # On recto pages without notes, align day name and day number to the right
            result = "\\hfill " + day_name + " \\hspace{0mm} " + day_number
    else:
        # On verso pages, place the day number to the left of the day name
        result += day_number + " \\hspace{0mm} " + day_name
        
        # Add notes at the end if present
        if notattext:
            result += "\\hfill \\small \\notescolor{" + notattext + "}"
    
    # Add newlines at the end
    result += "\n\n"
    
    return result

def generate_calendar_data():
    """
    Generates the complete calendar data structure for the year.
    
    Returns:
        list: A list of weeks, where each week contains a list of day data
    """
    vecka = spliceyear([])
    return purge(vecka)

def format_header(header_text, week_number, is_first_day=False, is_second_half=False):
    """
    Formats a header for a page or section of the calendar.
    
    Args:
        header_text (str): The header text (typically month and year)
        week_number (str): The week number
        is_first_day (bool): Whether this is the first day of the week
        is_second_half (bool): Whether this is the second half of the week
        
    Returns:
        str: Formatted LaTeX code for the header
    """
    header = []
    
    if is_second_half:
        header.append(f"\\hfill \\Large\\bfseries {header_text} \\normalfont\\normalsize\n\n")
    else:
        header.append(f"\\Large\\bfseries {header_text} \\hfill \\normalfont\\small {currweek} {week_number}\n\n")
    
    header.append("\\vspace{-4mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n")
    
    if is_first_day and not is_second_half:
        header.append(f"\\normalsize {thisweek}\n\n")
        
    return "".join(header)

def format_separator(stretch=1, is_pagebreak=False):
    """
    Formats a separator between days or pages.
    
    Args:
        stretch (float): The stretch factor for spacing
        is_pagebreak (bool): Whether to include a page break
        
    Returns:
        str: Formatted LaTeX code for the separator
    """
    if is_pagebreak:
        return f"\\vspace{{\\stretch{{{stretch}}}}}\\pagebreak\n\n"
    else:
        return f"\\vspace{{\\stretch{{{stretch}}}}}\\rule{{\\textwidth}}{{0.1pt}}\\vspace{{-2mm}}\n\n"

def preamble():  # This is the preamble
    """
    Generates the LaTeX preamble for the document.
    Configures document class, language, fonts, and custom commands.

    Returns:
        str: A LaTeX-formatted string containing the document preamble.
    """
    # Map language codes to babel language names
    language_map = {
        "en": "english",
        "de": "german",
        "sv": "swedish"
    }
    
    # Get proper babel language name, default to swedish if not found
    babel_language = language_map.get(language, "swedish")
    
    # Build the preamble using a list for better readability
    latex_lines = [
        "\\documentclass[11pt,titlepage]{article}",
        f"\\usepackage[{babel_language}]{{babel}}",
        "\\usepackage{fontspec}",
        "\\usepackage{graphicx}",
        "\\usepackage{parskip}",
        "\\usepackage{tikz}",
        "\\usepackage{pifont}",
        "\\usepackage[bookmarks=true,pdfborder={{0 0 0}}]{hyperref}",
        "\\usepackage[dvips=false,pdftex=false,vtex=false,twoside]{geometry}",
        "\\usepackage[cross,a4,center,dvips,noinfo,odd]{crop}",
        "\\defaultfontfeatures{Mapping=tex-text}",
        "\\setmainfont[BoldFont=Cronos Pro, ItalicFont=Cronos Pro Light Italic, " +
        "BoldItalicFont=Cronos Pro Semibold, SlantedFont=Cronos Pro Bold, SmallCapsFont=Cronos Pro Light, " +
        "SmallCapsFeatures={LetterSpace=1.15, Letters=SmallCaps}, Numbers={OldStyle, Proportional}, Scale=0.75] {Cronos Pro Light}",
        f"\\geometry{{paperwidth={paperwidth}mm, paperheight={paperheight}mm, margin={margin}mm, " +
        f"bottom={bottom}mm, top={top}mm, left={left}mm, nohead}}",
        "",
        "\\newcommand*\\circled[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=1pt," +
        "minimum height=4.5mm,minimum width=4.5mm, line width=0.1pt] (char) {#1};}}",
        ""
    ]
    
    # Add color-specific commands
    if color_mode == "color":
        latex_lines.extend([
            "\\newcommand*\\circledfill[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=0.1pt," +
            "minimum height=4.55mm,minimum width=4.55mm, line width=0.1pt, fill=red!60!black] (char) {#1};}}",
            "\\newcommand*\\notescolor[1]{\\textcolor{red!60!black}{#1}}",
            ""
        ])
    else:
        latex_lines.extend([
            "\\newcommand*\\circledfill[1]{\\tikz[baseline=(char.base)]{\\node[shape=circle,draw,inner sep=0.1pt," +
            "minimum height=4.55mm,minimum width=4.55mm, line width=0.1pt, fill=black] (char) {#1};}}",
            "\\newcommand*\\notescolor[1]{#1}",
            ""
        ])
    
    # Make the color_mode variable accessible globally
    global is_color_mode
    is_color_mode = (color_mode == "color")
    
    # Add final commands
    latex_lines.extend([
        "\\newcommand{\\tikzcircle}[2]{\\tikz[baseline=-0.5ex]\\draw[#2,radius=#1,ultra thin] (0,0) circle ;}",
        "\\pagenumbering{gobble}",
        ""
    ])
    
    # Join all lines with newlines
    return "\n".join(latex_lines)

def opening():
    """
    Generates the opening part of the LaTeX document.
    Creates the title page with year, document title, and author information.
    
    Returns:
        str: LaTeX code for document beginning and title page.
    """
    # Use f-strings for cleaner formatting
    latex = (
        "\\begin{document}\n\n"
        f"\\title{{\\bfseries\\itshape \\Huge {theyear} {year}\\\\ "
        f"\\vspace{{0.25em}} \\Large \\normalfont {titel}}}\n"
        f"\\author{{\\emph{{{av}}} Joakim Hertze}}\n"
        "\\maketitle\n\n"
        "\\pagebreak\n\n"
    )
    return latex
    
def closing():
    """
    Generates the closing part of the LaTeX document.
    
    Returns:
        str: LaTeX code to end the document.
    """
    return "\\end{document}\n\n"
    
def getmatter(filecontents):
    """
    Converts file contents into a single string for inclusion in the document.
    
    Args:
        filecontents (list): List of strings, typically lines read from a front/back matter file.
        
    Returns:
        str: A string with all lines joined by newlines, ready for insertion into LaTeX document.
    """
    if not filecontents:
        return ""
    
    return "\n".join(filecontents)
    
def week1pagenotes():
    """
    Generates a week-per-page layout with notes.
    
    Returns:
        str: Complete LaTeX code for the layout
    """
    latex_parts = []
    calendar_data = generate_calendar_data()
    
    # Page counter to track recto/verso pages
    page_counter = 0
    
    for week in calendar_data:
        week_number = getvecka(week[0])
        header_text = getheader(week[0:7])
        
        # Determine if this page is a recto page (odd pages are recto, even pages are verso)
        is_recto_page = (page_counter % 2 == 1)
        
        # Add week header
        latex_parts.append(format_header(header_text, week_number, is_first_day=False))
        
        # Add each day of the week
        for day_index, day in enumerate(week):
            note_text = notat(day)
            is_saturday = (day_index == 5)
            
            # All days on the same page should have the same alignment
            # based on whether the page is recto or verso
            latex_parts.append(format_day(day, note_text, is_saturday, is_recto=is_recto_page))
            
            # Add appropriate separator
            if day_index < 6:
                latex_parts.append(format_separator())
            else:
                latex_parts.append(format_separator(is_pagebreak=True))
                latex_parts.append(f"\\hfill \\small {notesden} \n\n")
                latex_parts.append("\\pagebreak\n\n")
        
        # Each week takes TWO pages (one for the week and one for notes)
        # So we need to increase the page counter by 2
        page_counter += 2
    
    return "".join(latex_parts)
def week2pages():
    """
    Generates a two-page-per-week layout.
    
    Returns:
        str: Complete LaTeX code for the layout
    """
    latex_parts = []
    calendar_data = generate_calendar_data()
    
    for week in calendar_data:
        week_number = getvecka(week[0])
        first_half_header = getheader(week[0:3])
        second_half_header = getheader(week[3:7])
        
        # Process first half of the week (Monday-Wednesday)
        latex_parts.append(format_header(first_half_header, week_number, is_first_day=True))
        latex_parts.append(format_separator(stretch=1))
        
        for day_index in range(3):
            day = week[day_index]
            note_text = notat(day)
            is_saturday = False  # First half never contains Saturday
            
            # Add the day (verso page)
            latex_parts.append(format_day(day, note_text, is_saturday, is_recto=False))
            
            # Add appropriate separator
            if day_index < 2:
                latex_parts.append(format_separator())
            else:
                latex_parts.append(format_separator(is_pagebreak=True))
        
        # Process second half of the week (Thursday-Sunday)
        latex_parts.append(format_header(second_half_header, "", is_second_half=True))
        
        for day_index in range(3, 7):
            day = week[day_index]
            note_text = notat(day)
            is_saturday = (day_index == 5)
            
            # Add the day (recto page)
            latex_parts.append(format_day(day, note_text, is_saturday, is_recto=True))
            
            # Add appropriate separator
            if day_index < 6:
                latex_parts.append(format_separator())
            else:
                latex_parts.append(format_separator(is_pagebreak=True))
    
    return "".join(latex_parts)

def week2pageswf():
    """
    Generates a two-page-per-week layout with flexible spacing.
    
    Returns:
        str: Complete LaTeX code for the layout
    """
    latex_parts = []
    calendar_data = generate_calendar_data()
    
    for week in calendar_data:
        week_number = getvecka(week[0])
        first_half_header = getheader(week[0:3])
        second_half_header = getheader(week[3:7])
        
        # Process first half of the week (Monday-Wednesday)
        latex_parts.append(format_header(first_half_header, week_number, is_first_day=True))
        latex_parts.append(format_separator(stretch=0.2))
        
        for day_index in range(3):
            day = week[day_index]
            note_text = notat(day)
            is_saturday = False  # First half never contains Saturday
            
            # Add the day (verso page)
            latex_parts.append(format_day(day, note_text, is_saturday, is_recto=False))
            
            # Add appropriate separator
            if day_index < 2:
                latex_parts.append(format_separator())
            else:
                latex_parts.append(format_separator(is_pagebreak=True))
        
        # Process second half of the week (Thursday-Sunday)
        latex_parts.append(format_header(second_half_header, "", is_second_half=True))
        
        for day_index in range(3, 7):
            day = week[day_index]
            note_text = notat(day)
            is_saturday = (day_index == 5)
            
            # Add the day (recto page)
            latex_parts.append(format_day(day, note_text, is_saturday, is_recto=True))
            
            # Add appropriate separator with custom stretch values
            if day_index < 5:
                latex_parts.append(format_separator())
            elif day_index == 5:
                latex_parts.append(format_separator(stretch=0.6))
            else:
                latex_parts.append(format_separator(stretch=0.6, is_pagebreak=True))
    
    return "".join(latex_parts)

def weekonepage():
    """
    Generates a week-per-page layout.
    
    Returns:
        str: Complete LaTeX code for the layout
    """
    latex_parts = []
    calendar_data = generate_calendar_data()
    
    # Page counter to track recto/verso pages
    page_counter = 0
    
    for week in calendar_data:
        week_number = getvecka(week[0])
        header_text = getheader(week[0:7])
        
        # Determine if this page is a recto page (odd pages are recto, even pages are verso)
        is_recto_page = (page_counter % 2 == 1)
        page_counter += 1
        
        # Add week header
        latex_parts.append(format_header(header_text, week_number))
        
        # Add each day of the week
        for day_index, day in enumerate(week):
            note_text = notat(day)
            is_saturday = (day_index == 5)
            
            # All days on the same page should have the same alignment
            # based on whether the page is recto or verso
            latex_parts.append(format_day(day, note_text, is_saturday, is_recto=is_recto_page))
            
            # Add appropriate separator
            if day_index < 6:
                latex_parts.append(format_separator())
            else:
                latex_parts.append(format_separator(is_pagebreak=True))
    
    return "".join(latex_parts)

def onedayperpage():
    """
    Generates a day-per-page layout.
    
    Returns:
        str: Complete LaTeX code for the layout
    """
    latex_parts = []
    calendar_data = generate_calendar_data()
    
    for week in calendar_data:
        for day_index, day in enumerate(week):
            week_number = getvecka(day)
            header_text = getheadersingle([day])
            note_text = notat(day)
            is_saturday = (day_index == 5)
            is_recto = (day_index % 2 == 1)  # Alternate recto/verso
            
            # Add day header
            latex_parts.append(format_header(header_text, week_number))
            
            # Add the day
            latex_parts.append(format_day(day, note_text, is_saturday, is_recto))
            
            # Always add a page break after each day
            latex_parts.append(format_separator(is_pagebreak=True))
    
    return "".join(latex_parts)


def weekgold():
    """
    Generates a 'gold' layout with specialized formatting for the week.
    Each week spans multiple pages with dedicated spaces for weeknotes and gratitude.
    
    Returns:
        str: Complete LaTeX code for the layout
    """
    latex_parts = []
    calendar_data = generate_calendar_data()
    
    for week in calendar_data:
        week_number = getvecka(week[0])
        versoheader1 = getheader(week[0:2])
        rectoheader1 = getheader(week[3:4])
        versoheader2 = getheader(week[5:7])
        rectoheader2 = getheader(week[5:7])
        
        # Get week note for this week
        weeknotattext = weeknotat(week_number)
        
        # Process each day of the week
        for day_index, day in enumerate(week):
            note_text = notat(day)
            is_saturday = (day_index == 5)
            
            if day_index < 3:  # Monday to Wednesday (verso page)
                if day_index == 0:  # Monday - add header
                    latex_parts.append(format_header(versoheader1, week_number, is_first_day=True))
                
                if day_index > 0:  # Add separator before Tuesday and Wednesday
                    latex_parts.append(format_separator())
                
                # Add the day
                latex_parts.append(format_day(day, note_text, is_saturday, is_recto=False))
                
                # End of Wednesday - add week dots and page break
                if day_index == 2:
                    latex_parts.append("\\vspace{\\stretch{1}}\n")
                    latex_parts.append(weekdots(3))
                    latex_parts.append("\\pagebreak\n\n")
            
            elif 2 < day_index < 5:  # Thursday and Friday (recto page)
                if day_index == 3:  # Thursday - add header
                    latex_parts.append(format_header(rectoheader1, "", is_second_half=True))
                
                # Add the day
                latex_parts.append(format_day(day, note_text, is_saturday, is_recto=True))
                
                # After Friday - add footnote symbol, week dots, and page break
                if day_index < 4:
                    latex_parts.append(format_separator())
                else:  # Friday
                    latex_parts.append("\\footnotesize \\ding{93} \n\n")
                    latex_parts.append("\\vspace{\\stretch{1}}\n")
                    latex_parts.append("\\hfill" + weekdots(5))
                    latex_parts.append("\\pagebreak\n\n")
            
            else:  # Saturday and Sunday
                if day_index == 5:  # Saturday - add header
                    latex_parts.append(format_header(versoheader2, week_number, is_first_day=False))
                
                # Add the day
                latex_parts.append(format_day(day, note_text, is_saturday, is_recto=False))
                
                # Add separator after Saturday
                if day_index < 6:
                    latex_parts.append(format_separator())
                else:  # End of Sunday
                    latex_parts.append("\\hfill \\footnotesize \\ding{93} \n\n")
                    latex_parts.append("\\vspace{\\stretch{1}}\n")
                    latex_parts.append(weekdots(7))
                    latex_parts.append("\\pagebreak\n\n")
                    
                    # Add gratitude page after Sunday
                    if day_index == 6:
                        latex_parts.append("\\hfill \\Large\\bfseries " + rectoheader2 + " \\normalfont\\normalsize\n\n")
                        latex_parts.append("\\vspace{-4.5mm}\\rule{\\textwidth}{0.4pt}\\vspace{-2mm}\n\n")
                        
                        # Add week notes if available
                        if weeknotattext:
                            latex_parts.append(weeknotattext + "\n\n")
                        
                        # Add gratitude section
                        latex_parts.append("\\vspace{\\stretch{3}}\\rule{2cm}{0.1pt}\n\n")
                        latex_parts.append("\\vspace{-2mm}" + gratitude + "\n\n")
                        latex_parts.append("\\vspace{\\stretch{1}}\n\n")
                        latex_parts.append("\\pagebreak\n\n")
    
    return "".join(latex_parts)

def weekdots(day):
    """
    Assembles week dots according to day.
    
    Args:
        day (int): The current day of the week (1-7)
        
    Returns:
        str: LaTeX code for the week dots
    """
    weekdots_code = ""
    for x in range(0, day):
        weekdots_code += "\\tikzcircle{2pt}{fill=black}\\hspace{2pt}"
    for x in range(day, 7):
        weekdots_code += "\\tikzcircle{2pt}{}\\hspace{2pt}"
    return weekdots_code

    
# Main script section - improved for readability and maintainability

def get_user_input(prompt, options, default=None):
    """
    Get and validate user input against a list of valid options.
    
    Args:
        prompt (str): The prompt to display to the user
        options (list): List of valid options
        default (str, optional): Default value if user presses Enter
        
    Returns:
        str: The validated user input
    """
    while True:
        user_input = input(prompt).strip().lower()
        if not user_input and default:
            return default
        if user_input in options:
            return user_input
        print(f"Please choose one of: {', '.join(options)}")

def get_year_input(prompt, default=None):
    """
    Get and validate a 4-digit year input from the user.
    
    Args:
        prompt (str): The prompt to display to the user
        default (int, optional): Default year if user presses Enter
        
    Returns:
        int: The validated year
    """
    while True:
        year_input = input(prompt)
        if not year_input and default:
            return default
        
        try:
            year = int(year_input)
            if re.match(r"^\d{4}$", str(year)):
                return year
            print("Please enter a valid 4-digit year.")
        except ValueError:
            print("Please enter a valid number.")

def parse_arguments(args):
    """
    Parse command-line arguments for the script.
    
    Args:
        args (str): The command-line arguments string
        
    Returns:
        dict: A dictionary containing all configuration settings
    """
    params = args.split("-")
    current_year = datetime.datetime.now().year
    
    config = {
        "paper": params[0] if len(params) > 0 else "personal",
        "color_mode": params[1] if len(params) > 1 else "bw",
        "layout": params[2] if len(params) > 2 else "w1p",
        "language": params[3] if len(params) > 3 else "en",
        "frontmatter": params[5] if len(params) > 5 else "no",
        "backmatter": params[6] if len(params) > 6 else "no",
        "dolatex": params[7] if len(params) > 7 else "no"
    }
    
    # Year needs special validation
    try:
        config["year"] = int(params[4]) if len(params) > 4 else current_year
    except (ValueError, IndexError):
        config["year"] = current_year
    
    return config

def set_paper_dimensions(paper):
    """
    Set paper dimensions based on the selected paper format.
    
    Args:
        paper (str): The selected paper format
        
    Returns:
        dict: A dictionary containing paper dimensions
    """
    dimensions = {
        "a5": {
            "paperheight": "212", "paperwidth": "150",
            "margin": "5.5", "left": "13.5", "top": "5.5", "bottom": "10"
        },
        "a6": {
            "paperheight": "150", "paperwidth": "107",
            "margin": "4", "left": "13", "top": "2", "bottom": "3.5"
        },
        "pocket": {
            "paperheight": "122", "paperwidth": "83",
            "margin": "4", "left": "9.5", "top": "3", "bottom": "4"
        },
        "personal": {
            "paperheight": "173", "paperwidth": "97",
            "margin": "3", "left": "11", "top": "2", "bottom": "3.5"
        }
    }
    
    return dimensions.get(paper, dimensions["personal"])

def set_language_strings(language, paper):
    """
    Set language-specific strings.
    
    Args:
        language (str): The selected language code
        paper (str): The selected paper format
        
    Returns:
        dict: A dictionary containing language-specific strings
    """
    strings = {
        "en": {
            "dayname": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            "monthname": ["January", "February", "March", "April", "May", "June", 
                          "July", "August", "September", "October", "November", "December"],
            "thisweek": "this week",
            "currweek": "week",
            "saturday": "saturday",
            "sunday": "sunday",
            "av": "by",
            "notesden": "notes",
            "theyear": "The Year",
            "titel": f"for {paper.title()} Size",
            "gratitude": "What have you felt grateful for this week?"
        },
        "de": {
            "dayname": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
            "monthname": ["Januar", "Februar", "März", "April", "Mai", "Juni", 
                         "Juli", "August", "September", "Oktober", "November", "Dezember"],
            "thisweek": "Diese Woche",
            "currweek": "Woche",
            "saturday": "Samstag",
            "sunday": "Sonntag",
            "av": "von",
            "notesden": "Notizen",
            "theyear": "Das Jahr",
            "titel": f"für {paper.title()} Size",
            "gratitude": "Wofür warst Du diese Woche dankbar?"
        },
        "sv": {
            "dayname": ["måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag", "söndag"],
            "monthname": ["januari", "februari", "mars", "april", "maj", "juni", 
                         "juli", "augusti", "september", "oktober", "november", "december"],
            "thisweek": "denna vecka",
            "currweek": "vecka",
            "saturday": "lördag",
            "sunday": "söndag",
            "av": "av",
            "notesden": "anteckningar",
            "theyear": "Året",
            "titel": f"för {paper.title()}",
            "gratitude": "Vad har du känt tacksamhet över denna vecka?"
        }
    }
    
    return strings.get(language, strings["sv"])

def load_supplementary_files(year, language, interactive=False):
    """
    Load supplementary files for the calendar.
    
    Args:
        year (int): The calendar year
        language (str): The selected language code
        interactive (bool): Whether to provide feedback in interactive mode
        
    Returns:
        tuple: Holidays, notes, and weeknotes data
    """
    year_str = str(year)
    
    # Load holidays
    holidays = readfile(f"holidays-{year_str}-{language}.txt")
    if holidays and interactive:
        print(f"\n--> I've successfully loaded *holidays-{year_str}-{language}.txt*.")
    
    # Load notes
    notes = readfile(f"notes-{year_str}-{language}.txt")
    if notes and interactive:
        print(f"\n--> I've successfully loaded *notes-{year_str}-{language}.txt*.")
    
    # Load week notes
    weeknotes = readfile(f"weeknotes-{year_str}-{language}.txt")
    if weeknotes and interactive:
        print(f"\n--> I've successfully loaded *weeknotes-{year_str}-{language}.txt*.")
    
    return holidays, notes, weeknotes

def assemble_diary(config, lang_strings, dimension_params, supplementary_files):
    """
    Assemble the diary LaTeX document.
    
    Args:
        config (dict): Configuration settings
        lang_strings (dict): Language-specific strings
        dimension_params (dict): Paper dimension parameters
        supplementary_files (tuple): Supplementary file data
        
    Returns:
        str: The complete LaTeX document
    """
    holidays, notes, weeknotes = supplementary_files
    
    # Set global variables needed by functions
    globals().update(lang_strings)
    globals().update(dimension_params)
    globals().update({
        "holidays": holidays,
        "notes": notes,
        "weeknotes": weeknotes,
        "year": config["year"],
        "color_mode": config["color_mode"],
        "language": config["language"]
    })
    
    # Start building the diary
    latex = preamble() + opening()
    
    # Add the appropriate layout
    if config["layout"] == "w2p":
        latex = latex + week2pages()
    elif config["layout"] == "w2pwf":
        latex = latex + week2pageswf()
    elif config["layout"] == "w1pnotes":
        latex = latex + week1pagenotes()
    elif config["layout"] == "1dp":
        latex = latex + onedayperpage()
    elif config["layout"] == "wg":
        latex = latex + weekgold()
    else:
        latex = latex + weekonepage()
    
    # Close the document
    latex = latex + closing()
    
    return latex

def save_and_compile(latex, config, interactive=False):
    """
    Save the LaTeX document and optionally compile it.
    
    Args:
        latex (str): The LaTeX document content
        config (dict): Configuration settings
        interactive (bool): Whether to provide feedback in interactive mode
    """
    # Create output filename
    filename = f"diary-{config['paper']}-{config['year']}-{config['language']}"
    
    # Write LaTeX to file
    with open(f"{filename}.tex", "w") as f:
        f.write(latex)
    
    if interactive:
        print(f"\nI've written the LaTeX document to *{filename}.tex*.")
    
    # Compile LaTeX to PDF if requested
    if config["dolatex"] == "yes":
        os.system(f"xelatex {filename}.tex")
        if interactive:
            print("\nYour file has been typeset.")
        os.system(f"open {filename}.pdf")

# Main script execution
if __name__ == "__main__":
    # Check if running in interactive mode or with arguments
    interactive_mode = len(sys.argv) < 2
    
    if interactive_mode:
        # Display welcome message
        print("\n\nA L F I E\n\nA somewhat clever diary generator for Filofax-sized binders")
        print("\n---------------------------------------------------------\n")
        print("\nHello,")
        print("\nI have some questions before we begin:\n")
        
        # Get user configuration
        current_year = datetime.datetime.now().year
        config = {
            "paper": get_user_input(
                "\n> What format should I use for your insert (pocket/personal/a5/a6)? [personal] ",
                ["pocket", "personal", "a5", "a6"], "personal"
            ),
            "color_mode": get_user_input(
                "\n> Should I use color or black & white mode (color/bw)? [bw] ",
                ["color", "bw"], "bw"
            ),
            "layout": get_user_input(
                "\n> What layout should I use for your insert (w1p/w1pnotes/w2p/w2pwf/1dp/wg)? [w2pwf] ",
                ["w1p", "w1pnotes", "w2p", "w2pwf", "1dp", "wg"], "w2pwf"
            ),
            "language": get_user_input(
                "\n> What language should I use (sv/de/en)? [sv] ",
                ["sv", "de", "en"], "sv"
            ),
            "year": get_year_input(
                f"\n> What year do you need (YYYY)? [{current_year}] ",
                current_year
            )
        }
    else:
        # Parse command-line arguments
        config = parse_arguments(sys.argv[1])
    
    # Set paper dimensions and language strings
    dimension_params = set_paper_dimensions(config["paper"])
    lang_strings = set_language_strings(config["language"], config["paper"])
    
    # Load supplementary files
    supplementary_files = load_supplementary_files(
        config["year"], config["language"], interactive_mode
    )
    
    # Assemble the diary
    if interactive_mode:
        print("\nI'm building your calendar now.")
    
    latex = assemble_diary(config, lang_strings, dimension_params, supplementary_files)
    
    if interactive_mode:
        print("\nDone!")
        # Ask about typesetting if in interactive mode
        config["dolatex"] = get_user_input(
            "\n> Shall I try to typeset your LaTeX document (yes/no)? [yes] ",
            ["yes", "no"], "yes"
        )
    
    # Save and compile
    save_and_compile(latex, config, interactive_mode)
    
    # Final message in interactive mode
    if interactive_mode:
        print("\n\nAll done!")
        print("\n\n---------------------------------------------------------\n\n")