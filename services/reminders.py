# -*- coding: utf-8 -*-

import datetime
import logging as log

import telegram

import secrets
from util import common


def remind():
    bot = telegram.Bot(secrets.bot_token)
    if (datetime.datetime.today() + datetime.timedelta(days=1)).date() not in common.no_trip_days:
        for chat_id in secrets.users:
            try:
                remind_user(bot, chat_id)
            except Exception as ex:
                log.info(f"Failed to alert {str(chat_id)}", ex)

        for chat_id in secrets.drivers:
            try:
                remind_driver(bot, chat_id)
            except Exception as ex:
                log.info(f"Failed to alert {str(chat_id)}", ex)


def remind_driver(bot, chat_id):
    """Questo comando verrà eseguito alle 23:30 di ogni giorno feriale."""
    today = datetime.datetime.today().weekday()
    if 0 <= (today + 1) % 7 <= 4:
        heading_sent = False
        message = []
        tomorrow = common.tomorrow()

        for direction in secrets.groups:
            if str(chat_id) in secrets.groups[direction][tomorrow] \
                    and not secrets.groups[direction][tomorrow][chat_id]["Suspended"]:
                # Mando il messaggio iniziale una sola volta
                if not heading_sent:
                    message.append("Sommario dei viaggi per domani:")
                    heading_sent = True

                trip = secrets.groups[direction][tomorrow][chat_id]
                permanent_people = ",".join(secrets.users[i]["Name"] for i in trip["Permanent"])
                temporary_people = ",".join(secrets.users[i]["Name"] for i in trip["Temporary"])
                message.append(f"\n\nViaggio {common.dir_name(direction)} - {trip['Time']}"
                               f"\n\nPermanentemente: {permanent_people}"
                               f"\nSolo domani: {temporary_people}")

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
                                 text=f"REMINDER: Domani hai un viaggio: "
                                      f"\n\n🚗: {str(secrets.users[driver]['Name'])}"
                                      f"\n🗓: {day}"
                                      f"\n🕓: {time}"
                                      f"\n➡: {common.dir_name(direction)}"
                                      f"\n🔁: {common.mode_name(mode)}")
