import getpass
import sys
from pprint import pprint

import requests.packages.urllib3

import constants
import curtin_estudent
import gcal
import scraper


def main():
    username = raw_input('OASIS Username: ')
    password = getpass.getpass('OASIS Password: ')
    separate_cal = question_yes_no("Do you want separate calendars for each unit?\n"
                                   "Choose yes if you are importing this calendar from Google into Apple's calendar app")
    if not separate_cal:
        calendar_name = raw_input('New calendar name: ')

    # Initialise session and scraper
    session = curtin_estudent.Session()
    getter = scraper.Scraper()
    # Login
    print('Logging in....')
    session.login(username, password)
    # Navigate to timetable
    print('Finding timetables')
    session.navigate_tt_page()
    # Scrape first timetable
    print('Scraping timetables')
    event_list = [getter.scrape_timetable_page(session.current_data)]
    # Scrape timetables until there are no more
    while getter.consecutive_empty_scrapes < 5:
        session.advance_tt_page_one_week()
        event_list.append(getter.scrape_timetable_page(session.current_data))
    # Select and attach the same colour to each unit
    print('Attaching unit colours')
    attach_colours_to_units(event_list)

    if separate_cal:
        cal_sep_list = create_unit_separated_cal_list(event_list)
        create_unit_separated_calendars(cal_sep_list)
    else:
        # Create and publish the calendar to Google Calendar
        print('Creating calendar')
        create_calendar(event_list, calendar_name)

    # Completed
    print('Successfully Completed')

def create_calendar(event_list, calendar_name):
    cal_id = gcal.create_calendar(calendar_name)
    for lst in event_list:
        for event in lst:
            gcal.add_event(event, cal_id)


def create_unit_separated_calendars(cal_sep_list):
    for unit_dict in cal_sep_list:
        cal_id = gcal.create_calendar(unit_dict.keys()[0])
        print("Creating calendar for: {}".format(unit_dict.keys()[0]))
        for event in unit_dict[unit_dict.keys()[0]]:
            gcal.add_event(event, cal_id)


def create_unit_separated_cal_list(event_list):
    cal_names = set()
    cal_lst = []

    # Go through all of the events and add the unit names to the set to get the individual calendar names
    for lst in event_list:
        for item in lst:
            unit_name = item['summary'].split()[0]
            cal_names.add(unit_name)

    for item in cal_names:
        cal_lst.append({
            item: []
        })

    pprint(cal_lst)

    for lst in event_list:
        for item in lst:
            unit_name = item['summary'].split()[0]
            for unit_dict in cal_lst:
                if unit_name in unit_dict:
                    unit_dict[unit_name].append(item)

    return (cal_lst)


def attach_colours_to_units(event_list):
    unit_names = []
    for lst in event_list:
        for item in lst:
            if item['summary'].split()[0] not in unit_names:
                unit_names.append(item['summary'].split()[0])
            item['colorId'] = constants.COLORS[unit_names.index(item['summary'].split()[0])]


def question_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n\n")


if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings()
    main()
