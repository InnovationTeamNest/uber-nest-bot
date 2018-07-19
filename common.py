# -*- coding: utf-8 -*-

import datetime
import time
import secrets


def today():
    return day_to_string(datetime.datetime.today().weekday())


def tomorrow():
    return day_to_string(datetime.datetime.today().weekday() + 1)


def day_to_string(input):
    date = (input) % 7
    if date == 0:
        return u"Lunedi"
    elif date == 1:
        return u'Martedi'
    elif date == 2:
        return u"Mercoledi"
    elif date == 3:
        return u"Giovedi"
    elif date == 4:
        return u"Venerdi"
    elif date == 5:
        return u"Sabato"
    elif date == 6:
        return u"Domenica"


def string_to_day(input):
    if input == u"Lunedi":
        return 0
    elif input == u"Martedi":
        return 1
    elif input == u"Mercoledi":
        return 2
    elif input == u"Giovedi":
        return 3
    elif input == u"Venerdi":
        return 4
    elif input == u"Sabato":
        return 5
    elif input == u"Domenica":
        return 6


def is_weekday(input):
    return 0 <= string_to_day(input) <= 4


def is_dst():
    return time.localtime().tm_isdst


def get_partenza(driver, day, direction):
    output = None
    try:
        if direction == "Salita":
            output = str(secrets.groups_morning[day][driver]["Time"].encode('utf-8') + " per Povo")
        elif direction == "Discesa":
            output = str(secrets.groups_evening[day][driver]["Time"].encode('utf-8') + " per NEST")
    except KeyError as ex:
        output = None
    return output


def search_by_booking(person):
    groups = secrets.groups_morning
    data = [["Salita", date, driver, mode] for date in groups for driver in groups[date]
            for mode in groups[date][driver] if person in groups[date][driver][mode]]

    groups = secrets.groups_evening
    data.extend([["Discesa", date, driver, mode] for date in groups for driver in groups[date]
                for mode in groups[date][driver] if person in groups[date][driver][mode]])

    return data
