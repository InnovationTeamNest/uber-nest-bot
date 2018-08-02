# -*- coding: utf-8 -*-

import datetime
import common
import secrets

from decimal import Decimal


def process_debits():  # Questo comando verrà fatto partire alle 02:00 di ogni giorno
    today = datetime.datetime.today().weekday()
    if 1 <= today <= 5:
        for direction in secrets.groups:
            trips = secrets.groups[direction][common.day_to_string(today - 1)]
            for driver in trips:
                for mode in trips[driver]:
                    if mode != u"Time":
                        for user in trips[driver][mode]:
                            try:
                                secrets.users[user][u"Debit"][driver] += Decimal(secrets.trip_price)
                            except KeyError:
                                secrets.users[user][u"Debit"][driver] = Decimal(secrets.trip_price)
                trips[driver][u"Temporary"] = {}


def edit_money(bot, update):
    if str(update.message.chat_id) == secrets.owner_id:
        pass  # Per modificare a mano i soldi


def get_credits(input_creditor):
    return [(user, secrets.users[user][u"Debit"][creditor]) for user in secrets.users
            for creditor in secrets.users[user][u"Debit"] if creditor == input_creditor]


def get_debits(input_debitor):
    return [(creditor, secrets.users[input_debitor][u"Debit"][creditor])
            for creditor in secrets.users[input_debitor][u"Debit"]]
