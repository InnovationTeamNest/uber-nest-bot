# -*- coding: utf-8 -*-

import datetime
import logging as log

import data.data_api
from data.data_api import all_users, is_driver, all_directions, get_trip_group, get_name
from util import common


def remind():
    from routing.webhook import BotUtils
    bot = BotUtils.bot

    today = datetime.datetime.today()

    if 0 <= (today.weekday() + 1) % 7 <= 4 and (today + datetime.timedelta(days=1)).date() \
            not in common.no_trip_days:
        # Il comando va eseguito solo nei giorni feriali e comunque non
        # nei giorni esplicitamente segnati in secrets.py
        for chat_id in all_users():
            try:
                remind_user(bot, chat_id)
            except Exception as ex:
                log.critical(f"Failed to alert {chat_id}")
                log.critical(ex)

            if is_driver(chat_id):
                try:
                    remind_driver(bot, chat_id)
                except Exception as ex:
                    log.critical(f"Failed to alert driver {chat_id}")
                    log.critical(ex)


def remind_driver(bot, chat_id):
    """Questo comando verrà eseguito alle 23:30 di ogni giorno feriale."""
    message = []

    for direction in all_directions():
        trip = get_trip_group(direction, common.tomorrow())
        if chat_id in trip and not trip[chat_id]["Suspended"]:
            # Mando il messaggio iniziale una sola volta
            if not message:
                message.append("⚠ Sommario dei tuoi viaggi di domani:")

            trip = trip[chat_id]
            permanent_people = ", ".join(f"[{get_name(user)}](tg://user?id={user})"
                                         for user in trip["Permanent"])
            temporary_people = ", ".join(f"[{get_name(user)}](tg://user?id={user})"
                                         for user in trip["Temporary"])

            message.append(f"\n\n🕓 {trip['Time']}"
                           f"\n{common.dir_name(direction)}"
                           f"\n👥 permanenti: {permanent_people}"
                           f"\n👥 temporanei: {temporary_people}")

    if message:
        bot.send_message(chat_id=chat_id, text="".join(message), parse_mode="Markdown")


def remind_user(bot, chat_id):
    """Questo comando verrà eseguito alle 23:30 di ogni giorno feriale"""
    bookings = data.data_api.get_bookings_day_nosusp(chat_id, common.tomorrow())

    message = []
    for item in bookings:
        if not message:
            message.append("⚠ Sommario dei tuoi viaggi di domani:")

        direction, driver, mode, time = item
        message.append(f"\n\n🚗 [{get_name(driver)}](tg://user?id={driver})"
                       f"\n🕓 {time}"
                       f"\n {common.dir_name(direction)}"
                       f"\n{common.mode_name(mode)}")

    if message:
        bot.send_message(chat_id=chat_id, text="".join(message), parse_mode="Markdown")
