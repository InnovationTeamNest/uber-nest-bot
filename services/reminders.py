# -*- coding: utf-8 -*-

import datetime
import logging as log

import telegram

import secrets
from util import common


def remind():
    bot = telegram.Bot(secrets.bot_token)
    today = datetime.datetime.today()

    if 0 <= (today.weekday() + 1) % 7 <= 4 and (today + datetime.timedelta(days=1)).date() \
            not in common.no_trip_days:
        # Il comando va eseguito solo nei giorni feriali e comunque non
        # nei giorni esplicitamente segnati in secrets.py
        for chat_id in secrets.users:
            try:
                remind_user(bot, chat_id)
            except Exception as ex:
                log.error(f"Failed to alert {chat_id}")
                log.error(ex)

            if chat_id in secrets.drivers:
                try:
                    remind_driver(bot, chat_id)
                except Exception as ex:
                    log.error(f"Failed to alert driver {chat_id}")
                    log.error(ex)


def remind_driver(bot, chat_id):
    """Questo comando verrà eseguito alle 23:30 di ogni giorno feriale."""
    message = []

    for direction in secrets.groups:
        trip = secrets.groups[direction][common.tomorrow()]
        if chat_id in trip and not trip[chat_id]["Suspended"]:
            # Mando il messaggio iniziale una sola volta
            if not message:
                message.append("⚠ Sommario dei tuoi viaggi di domani:")

            trip = trip[chat_id]
            permanent_people = ",".join(f"[{secrets.users[user]['Name']}](tg://user?id={user})"
                                        for user in trip["Permanent"])
            temporary_people = ",".join(f"[{secrets.users[user]['Name']}](tg://user?id={user})"
                                        for user in trip["Temporary"])

            message.append(f"\n\n🕓 {trip['Time']}"
                           f"\n{common.dir_name(direction)}"
                           f"\n👥 permanenti: {permanent_people}"
                           f"\n👥 temporanei: {temporary_people}")

    if message:
        bot.send_message(chat_id=chat_id, text="".join(message), parse_mode="Markdown")


def remind_user(bot, chat_id):
    """Questo comando verrà eseguito alle 23:30 di ogni giorno feriale"""
    bookings = common.sbp_day_nosusp(chat_id, common.tomorrow())

    message = []
    for item in bookings:
        if not message:
            message.append("⚠ Sommario dei tuoi viaggi di domani:")

        direction, driver, mode, time = item
        message.append(f"\n\n🚗 [{secrets.users[driver]['Name']}](tg://user?id={driver})"
                       f"\n🕓 {time}"
                       f"\n {common.dir_name(direction)}"
                       f"\n{common.mode_name(mode)}")

    if message:
        bot.send_message(chat_id=chat_id, text="".join(message), parse_mode="Markdown")
