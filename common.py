# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import time
import logging as log

from secret_data import groups, drivers


days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
work_days = days[:5]
booking_start = 5
booking_end = 23


def today():
    return day_to_string(datetime.datetime.today().weekday())


def tomorrow():
    return day_to_string(datetime.datetime.today().weekday() + 1)


def day_to_string(number):
    return days[number % 7]


def string_to_day(string):
    try:
        return days.index(string)
    except ValueError as ex:
        return " - "


def is_weekday(string):
    return 0 <= string_to_day(string) <= 4


def is_dst():
    return time.localtime().tm_isdst


def get_trip_time(driver, date, direction):
    try:
        output = str(groups[direction][date][driver]["Time"] + " " + direction_to_name(direction))
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


def search_by_booking(person, include_today=False):
    data = []

    for direction in groups:
        data.extend([[direction, day, driver, mode]
                     for day in groups[direction]
                     for driver in groups[direction][day]
                     for mode in groups[direction][day][driver]
                     if person in groups[direction][day][driver][mode]])

    if not include_today:
        for booking in data:
            if booking[1] == today():  # Il secondo elemento è il giorno
                data.remove(booking)

    return data


def booking_time():
    #  now = (datetime.datetime.now() + datetime.timedelta(hours=is_dst())).time()
    now = datetime.datetime.now().time()
    return (datetime.time(booking_start, 0) <= now <= datetime.time(booking_end, 0)) and is_weekday(tomorrow())


def localize_direction(mode):
    if mode == "Temporary":
        return "Temporanea"
    elif mode == "Permanent":
        return "Permanente"
    else:
        return " - "


def delete_driver(chat_id):
    del drivers[str(chat_id)]

    for direction in groups:
        for day in groups[direction]:
            if str(chat_id) in groups[direction][day]:
                del groups[direction][day][str(chat_id)]
