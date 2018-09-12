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
    """Questo comando verrà eseguito alle 23:30 di ogni giorno feriale"""
    today = datetime.datetime.today().weekday()
    if 0 <= (today + 1) % 7 <= 4:
        heading_sent = False

        for direction in secret_data.groups:
            if str(chat_id) in secret_data.groups[direction][common.tomorrow()]:
                # Mando il messaggio iniziale una sola volta
                if not heading_sent:
                    bot.send_message(chat_id=chat_id, text="Sommario dei viaggi per domani:")
                    heading_sent = True

                trip = secret_data.groups[direction][common.tomorrow()][str(chat_id)]
                bot.send_message(chat_id=chat_id,
                                 text="Viaggio " + common.direction_to_name(direction) + " - " + trip["Time"] + "\n\n" +
                                      "Permanentemente: " + ",".join(secret_data.users[i]["Name"]
                                                                     for i in trip["Permanent"]) + "\n" +
                                      "Solo domani: " + ",".join(secret_data.users[i]["Name"]
                                                                 for i in trip["Temporary"]))


def remind_user(bot, chat_id):
    """Questo comando verrà eseguito alle 23:30 di ogni giorno feriale"""
    bookings = common.search_by_booking(str(chat_id))

    today = datetime.datetime.today().weekday()
    if 0 <= (today + 1) % 7 <= 4:
        for item in bookings:
            direction, day, driver, mode = item
            if day == common.tomorrow():
                bot.send_message(chat_id=chat_id,
                                 text="REMINDER: Domani hai un viaggio " + common.direction_to_name(direction) +
                                      " alle ore " + common.get_trip_time(driver, day, direction) + " " +
                                      common.direction_to_name(direction) + " con " + str(secret_data.users[driver]))
