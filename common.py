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


def is_today_weekday():
    return 0 <= datetime.datetime.today().weekday() <= 4


def is_tomorrow_weekday():
    return 0 <= datetime.datetime.today().weekday() + 1 <= 4


def is_dst():
    return time.localtime().tm_isdst


def get_partenza(person, day, hour):
    output = None
    try:
        if hour == "Salita":
            output = str(secrets.times_morning[day][person].encode('utf-8') + " per Povo")
        elif hour == "Discesa":
            output = str(secrets.times_evening[day][person].encode('utf-8') + " per NEST")
    except KeyError as ex:
        output = None
    return output
