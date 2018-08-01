# -*- coding: utf-8 -*-

import datetime
import common
from secrets import groups, users


def process_debits():  # Questo comando verrà fatto partire alle 02:00 di ogni giorno
    today = datetime.datetime.today().weekday()
    if 1 <= today <= 5:
        for direction in groups:
            trips = groups[direction][common.day_to_string(today-1)]
            for driver in trips:
                for mode in trips[driver]:
                    if mode != u"Time":
                        for user in trips[driver][mode]:
                            try:
                                users[user][u"Debit"][driver] += 0.5
                            except KeyError:
                                users[user][u"Debit"][driver] = 0.5
                trips[driver][u"Temporary"] = {}


def edit_money():
    pass


def find_debits():
    pass
