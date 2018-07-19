# -*- coding: utf-8 -*-

import datetime
import time
import logging as log

from secrets import groups


def today():
    return day_to_string(datetime.datetime.today().weekday())


def tomorrow():
    return day_to_string(datetime.datetime.today().weekday() + 1)


def day_to_string(day_number):
    date = day_number % 7
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


def string_to_day(string):
    if string == u"Lunedi":
        return 0
    elif string == u"Martedi":
        return 1
    elif string == u"Mercoledi":
        return 2
    elif string == u"Giovedi":
        return 3
    elif string == u"Venerdi":
        return 4
    elif string == u"Sabato":
        return 5
    elif string == u"Domenica":
        return 6


def is_weekday(string):
    return 0 <= string_to_day(string) <= 4


def is_dst():
    return time.localtime().tm_isdst


def get_partenza(driver, date, direction):
    try:
        output = str(groups[direction][date][driver]["Time"].encode('utf-8') + " " + direction_to_name(direction))
    except KeyError as ex:
        log.info("Nessuna partenza trovata!" + ex.message)
        output = None
    return output


def direction_to_name(direction):
    if direction == "Salita":
        return "per Povo"
    elif direction == "Discesa":
        return "per il NEST"
    else:
        return " - "


def search_by_booking(person):
    data = []
    
    for direction in groups:
        data.extend([[direction, date, driver, mode] for date in groups[direction] for driver in groups[direction][date]
                    for mode in groups[direction][date][driver] if person in groups[direction][date][driver][mode]])

    return data
