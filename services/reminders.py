# -*- coding: utf-8 -*-

import datetime
import sys

import telegram

import secret_data
from util import common


def remind():
    bot = telegram.Bot(secret_data.bot_token)
    for chat_id in secret_data.users:
        try:
            remind_user(bot, chat_id)
        except Exception as ex:
            print("Failed to alert " + str(chat_id) + "\n\n", ex, file=sys.stderr)

    for chat_id in secret_data.drivers:
        try:
            remind_driver(bot, chat_id)
        except Exception as ex:
            print("Failed to alert " + str(chat_id) + "\n\n", ex, file=sys.stderr)


def remind_driver(bot, chat_id):
    """Questo comando verrà eseguito alle 23:30 di ogni giorno feriale."""
    today = datetime.datetime.today().weekday()
    if 0 <= (today + 1) % 7 <= 4:
        heading_sent = False
        message = ""
        tomorrow = common.tomorrow()

        for direction in secret_data.groups:
            if str(chat_id) in secret_data.groups[direction][tomorrow] \
                    and not secret_data.groups[direction][tomorrow][chat_id]["Suspended"]:
                # Mando il messaggio iniziale una sola volta
                if not heading_sent:
                    message += "Sommario dei viaggi per domani:"
                    heading_sent = True

                trip = secret_data.groups[direction][tomorrow][chat_id]
                message += "\n\nViaggio " + common.direction_to_name(direction) \
                           + " - " + trip["Time"] \
                           + "\n\n" + "Permanentemente: " + ",".join(secret_data.users[i]["Name"]
                                                                     for i in trip["Permanent"]) \
                           + "\n" + "Solo domani: " + ",".join(secret_data.users[i]["Name"]
                                                               for i in trip["Temporary"])

        if heading_sent:
            bot.send_message(chat_id=chat_id, text=message)


def remind_user(bot, chat_id):
    """Questo comando verrà eseguito alle 23:30 di ogni giorno feriale"""
    bookings = common.search_by_booking(chat_id)

    today = datetime.datetime.today().weekday()
    if 0 <= (today + 1) % 7 <= 4:
        for item in bookings:
            direction, day, driver, mode, time = item
            if day == common.tomorrow() and mode != "SuspendedUsers":
                bot.send_message(chat_id=chat_id,
                                 text="REMINDER: Domani hai un viaggio: "
                                      + "\n\n🚗: " + str(secret_data.users[driver]["Name"])
                                      + "\n🗓: " + day
                                      + "\n🕓: " + time
                                      + "\n➡: " + common.direction_to_name(direction)
                                      + "\n🔁: " + common.localize_mode(mode))
