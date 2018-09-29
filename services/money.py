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


class WeeklyReportHandler(webapp2.RequestHandler):
    def get(self):
        dumpable.get_data()
        weekly_report()
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
                                                  + " EUR da " + str(secret_data.users[driver]["Name"]) + ". ")
                            bot.send_message(chat_id=str(driver),
                                             text="Hai ora un credito di " + str(common.trip_price)
                                                  + " EUR da parte di " + str(secret_data.users[user]["Name"]))
                            log.debug(user + "'s debit from "
                                      + driver + " = " + str(secret_data.users[user]["Debit"][driver]))
                trips[driver]["Temporary"] = []


def weekly_report():
    """Questo comando viene fatto partire ogni sabato alle 10.00"""
    for user in secret_data.users:
        # Invio dei debiti per tutti gli utenti
        debits = get_debits(user)
        if debits:
            string = "Riepilogo settimanale dei debiti:\n"
            for name, value in debits:
                string = string + "\n" + secret_data.users[name]["Name"] + " - " + str(value) + " EUR"
            bot.send_message(chat_id=user, text=string)

        # Invio dei crediti per ogni singolo autista
        if user in secret_data.drivers:
            credits = get_credits(user)
            if credits:
                string = "Riepilogo settimanale dei crediti:\n"
                for name, value in credits:
                    string = string + "\n" + secret_data.users[name]["Name"] + " - " + str(value) + " EUR"
                bot.send_message(chat_id=user, text=string)


def get_credits(input_creditor):
    """Restituisce un array di tuple contenente, dato un creditore, gli ID dei debitori e il valore."""
    return [(user, secret_data.users[user]["Debit"][creditor]) for user in secret_data.users
            for creditor in secret_data.users[user]["Debit"] if creditor == input_creditor]


def get_debits(input_debitor):
    """Restituisce un array di tuple contenente, dato un debitore, gli ID dei creditore e il valore."""
    return [(creditor, secret_data.users[input_debitor]["Debit"][creditor])
            for creditor in secret_data.users[input_debitor]["Debit"]]
