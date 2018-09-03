# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import logging as log
import pytz

from secret_data import groups, drivers

#  Queste stringhe vengono utilizzate da tutto il programma

days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
work_days = days[:5]

booking_start = 5
booking_end = 23

direction_name = ["per Povo", "per il NEST"]
direction_generic = ["Salita", "Discesa"]

booking_types = ["Temporary", "Permanent"]
booking_types_localized = ["Temporanea", "Permanente"]

empty_str = " - "


def today():
    return day_to_string(datetime.datetime.today().weekday())


def tomorrow():
    return day_to_string(datetime.datetime.today().weekday() + 1)


def day_to_string(number):
    return days[number % 7]


def string_to_day(string):
    try:
        return days.index(string)
    except ValueError:
        return empty_str


def is_weekday(string):
    return 0 <= string_to_day(string) <= 4


def now_time():
    """Ritorna l'orario corrente con DST"""
    return (datetime.datetime.now() + datetime.timedelta(hours=1 + is_dst())).time()


def is_dst():
    return pytz.timezone("Europe/Rome").localize(datetime.datetime.now()).dst() == datetime.timedelta(0, 3600)


def direction_to_name(direction):
    try:
        return direction_name[direction_generic.index(direction)]
    except ValueError:
        return empty_str


def localize_mode(mode):
    try:
        return booking_types_localized[booking_types.index(mode)]
    except ValueError:
        return empty_str


def get_trip_time(driver, date, direction):
    try:
        output = str(groups[direction][date][driver]["Time"])
    except KeyError:
        log.debug("Nessuna partenza trovata in data - Oggetto della ricerca: "
                  + str(direction) + ", " + str(date) + ", " + str(driver))
        output = None
    return output


def search_by_booking(person):
    data = []
    for direction in groups:
        data.extend([[direction, day, driver, mode]
                     for day in groups[direction]
                     for driver in groups[direction][day]
                     for mode in groups[direction][day][driver]
                     if person in groups[direction][day][driver][mode]])
    return data


def booking_time():
    return is_weekday(tomorrow()) and datetime.time(booking_start, 0) <= now_time() <= datetime.time(booking_end, 0)


def delete_driver(chat_id):
    del drivers[str(chat_id)]

    for direction in groups:
        for day in groups[direction]:
            if str(chat_id) in groups[direction][day]:
                del groups[direction][day][str(chat_id)]
