# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

import telegram

import common
import secret_data


def remind():
    bot = telegram.Bot(secret_data.bot_token)
    for chat_id in secret_data.users:
        remind_user(bot, chat_id)
    for chat_id in secret_data.drivers:
        remind_driver(bot, chat_id)


def remind_driver(bot, chat_id):
    # Questo comando verrà eseguito alle 06:00 di ogni giorno feriale
    today = datetime.datetime.today().weekday()
    if 0 <= today <= 4:
        bot.send_message(chat_id=chat_id,
                         text="Sommario dei viaggi per oggi:")

        for direction in secret_data.groups:
            if str(chat_id) in secret_data.groups[direction][common.today()]:
                trip = secret_data.groups[direction][common.today()][str(chat_id)]
                bot.send_message(chat_id=chat_id,
                                 text="Viaggio " + common.direction_to_name(direction) + " - " + trip["Time"] + "\n\n" +
                                      "Permanentemente: " + ",".join(trip["Permanent"]) + "\n" +
                                      "Solo oggi: " + ",".join(trip["Temporary"]))


def remind_user(bot, chat_id):
    # Questo comando verrà eseguito alle 01:00 di ogni giorno feriale
    bookings = common.search_by_booking(str(chat_id))

    today = datetime.datetime.today().weekday()
    if 0 <= today <= 4:
        for item in bookings:
            direction, day, driver, mode = item
            if day == common.today():
                bot.send_message(chat_id=chat_id,
                                 text="REMINDER: Oggi hai un viaggio " + common.direction_to_name(direction) +
                                      " alle ore " + common.get_trip_time(driver, day, direction) + " " +
                                      common.direction_to_name(direction) + " con " + str(driver))
