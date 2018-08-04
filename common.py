# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import time
import logging as log

from secret_data import groups, drivers


def today():
    return day_to_string(datetime.datetime.today().weekday())


def tomorrow():
    return day_to_string(datetime.datetime.today().weekday() + 1)


def day_to_string(number):
    day = number % 7
    if day == 0:
        return "Lunedì"
    elif day == 1:
        return "Martedì"
    elif day == 2:
        return "Mercoledì"
    elif day == 3:
        return "Giovedì"
    elif day == 4:
        return "Venerdì"
    elif day == 5:
        return "Sabato"
    elif day == 6:
        return "Domenica"


def string_to_day(string):
    if string == "Lunedì":
        return 0
    elif string == "Martedì":
        return 1
    elif string == "Mercoledì":
        return 2
    elif string == "Giovedì":
        return 3
    elif string == "Venerdì":
        return 4
    elif string == "Sabato":
        return 5
    elif string == "Domenica":
        return 6


def is_weekday(string):
    return 0 <= string_to_day(string) <= 4


def is_dst():
    return time.localtime().tm_isdst


def get_partenza(driver, date, direction):
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
        data.extend([[direction, date, driver, mode] for date in groups[direction] for driver in groups[direction][date]
                     for mode in groups[direction][date][driver] if person in groups[direction][date][driver][mode]])

    if not include_today:
        for booking in data:
            if booking[1] == today():
                data.remove(booking)

    return data


def booking_time():
    now = (datetime.datetime.now() + datetime.timedelta(hours=1 + is_dst())).time()
    return (datetime.time(6, 0) <= now <= datetime.time(20, 0)) and is_weekday(tomorrow())


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
