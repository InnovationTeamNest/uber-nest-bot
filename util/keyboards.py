# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging as log

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import secret_data
from util import filters, common


def me_keyboard(update):
    keyboard = []
    if str(update.message.chat_id) in secret_data.drivers:
        money_string = "Gestire i miei debiti e i miei crediti"
        driver_string = "Smettere di essere un autista di UberNEST"
        keyboard.append([InlineKeyboardButton("Visualizzare e cancellare i miei viaggi",
                                              callback_data=filters.create_callback_data("ME", "TRIPS"))])
        keyboard.append([InlineKeyboardButton("Modificare il numero di posti della mia auto",
                                              callback_data=filters.create_callback_data("ME", "SLOTSDRIVER"))])
        keyboard.append([InlineKeyboardButton("Modificare il messaggio per i passeggeri",
                                              callback_data=filters.create_callback_data("ME", "MESSAGE"))])
    else:
        money_string = "Gestire i miei debiti"
        driver_string = "Diventare un autista di UberNEST"

    keyboard.append([InlineKeyboardButton(money_string,
                                          callback_data=filters.create_callback_data("MONEY"))])
    keyboard.append([InlineKeyboardButton(driver_string,
                                          callback_data=filters.create_callback_data("ME", "DRIVER"))])
    keyboard.append([InlineKeyboardButton("Cancellarmi dal sistema di UberNEST",
                                          callback_data=filters.create_callback_data("ME", "REMOVAL"))])
    keyboard.append([InlineKeyboardButton("Uscire dal menu",
                                          callback_data=filters.create_callback_data("CANCEL"))])
    return InlineKeyboardMarkup(keyboard)


def trips_keyboard(update):
    user = str(update.callback_query.from_user.id)
    keyboard = [[InlineKeyboardButton("Aggiungi un nuovo viaggio",
                                      callback_data=filters.create_callback_data("TRIPS", "ADD"))]]

    for day in common.work_days:
        for direction in secret_data.groups:
            time = common.get_trip_time(user, day, direction)
            if time is not None:
                group = secret_data.groups[direction][day][user]
                occupied_slots = len(group["Permanent"]) + len(group["Temporary"])
                keyboard.append(
                    [InlineKeyboardButton(day + ": " + time + " " + common.direction_to_name(direction)
                                          + " (" + str(occupied_slots) + ")",
                                          callback_data=filters.create_callback_data("TRIPS", "DELETE",
                                                                                     direction, day))])

    keyboard.append([InlineKeyboardButton("Esci", callback_data=filters.create_callback_data("CANCEL"))])
    return InlineKeyboardMarkup(keyboard)


def message_keyboard(update):
    user = str(update.callback_query.from_user.id)
    keyboard = []

    for day in common.work_days:
        for direction in secret_data.groups:
            time = common.get_trip_time(user, day, direction)
            if time is not None:
                group = secret_data.groups[direction][day][user]
                occupied_slots = len(group["Permanent"]) + len(group["Temporary"])
                keyboard.append(
                    [InlineKeyboardButton(day + ": " + time + " " + common.direction_to_name(direction)
                                          + " (" + str(occupied_slots) + ")",
                                          callback_data=filters.create_callback_data("MESSAGE", "EDIT",
                                                                                     direction, day))])

    keyboard.append([InlineKeyboardButton("Esci", callback_data=filters.create_callback_data("CANCEL"))])
    return InlineKeyboardMarkup(keyboard)


# Keyboard customizzata per visualizzare le prenotazioni in maniera inline
# Day è un oggetto di tipo stringa

def booking_keyboard(mode, day):
    keyboard = []

    for direction in secret_data.groups:
        for driver in secret_data.groups[direction][day]:
            try:
                keyboard.append(
                    [InlineKeyboardButton(
                        secret_data.users[driver]["Name"] + " - "
                        + common.get_trip_time(driver, day, direction)
                        + " " + common.direction_to_name(direction),
                        callback_data=filters.create_callback_data(
                            "BOOKING", direction, day, driver, mode))])
            except TypeError:
                log.debug("No bookings found")

    keyboard.append([InlineKeyboardButton("Annulla", callback_data=filters.create_callback_data("CANCEL"))])
    return InlineKeyboardMarkup(keyboard)
