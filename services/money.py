# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import logging as log

import webapp2
from telegram import Bot

import dumpable
import secret_data
from util import common

bot = Bot(secret_data.bot_token)


class MoneyHandler(webapp2.RequestHandler):
    def get(self):
        dumpable.get_data()
        process_debits()
        dumpable.dump_data()
        self.response.write("See console for output.")


def process_debits():
    """Questo comando verrà fatto partire alle 02:00 di ogni giorno"""
    today = datetime.datetime.today()
    if 1 <= today.weekday() <= 5 and today.date() not in common.no_trip_days:
        for direction in secret_data.groups:
            trips = secret_data.groups[direction][common.day_to_string(today.weekday() - 1)]
            for driver in trips:
                for mode in trips[driver]:
                    if mode == "Temporary" or mode == "Permanent":
                        for user in trips[driver][mode]:
                            try:
                                secret_data.users[user]["Debit"][driver] += common.trip_price
                            except KeyError:
                                secret_data.users[user]["Debit"][driver] = common.trip_price
                            bot.send_message(chat_id=str(user),
                                             text="Ti sono stati addebitati " + str(common.trip_price)
                                                  + " EUR da " + str(secret_data.users[driver]["Name"]))
                            bot.send_message(chat_id=str(driver),
                                             text="Hai ora un credito di " + str(common.trip_price)
                                                  + " EUR da parte di " + str(secret_data.users[user]["Name"]))
                            log.debug(user + "'s debit from "
                                      + driver + " = " + str(secret_data.users[user]["Debit"][driver]))
                trips[driver]["Temporary"] = []


def get_credits(input_creditor):
    return [(user, secret_data.users[user]["Debit"][creditor]) for user in secret_data.users
            for creditor in secret_data.users[user]["Debit"] if creditor == input_creditor]


def get_debits(input_debitor):
    return [(creditor, secret_data.users[input_debitor]["Debit"][creditor])
            for creditor in secret_data.users[input_debitor]["Debit"]]
