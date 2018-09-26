# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging as log

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import secret_data
from util import common
from util.filters import create_callback_data as ccd


def me_keyboard(chat_id):
    keyboard = []
    if str(chat_id) in secret_data.drivers:
        money_string = "Gestire i miei debiti e crediti"
        driver_string = "Smettere di essere un autista"
        keyboard.append([InlineKeyboardButton("Gestire i miei viaggi", callback_data=ccd("ME", "TRIPS"))])
        keyboard.append([InlineKeyboardButton("Modificare il numero di posti",
                                              callback_data=ccd("ME", "EDIT_DRIVER_SLOTS"))])
    else:
        money_string = "Gestire i miei debiti"
        driver_string = "Diventare un autista"

    keyboard.append([InlineKeyboardButton(money_string, callback_data=ccd("MONEY"))])
    keyboard.append([InlineKeyboardButton(driver_string, callback_data=ccd("ME", "DRIVER"))])
    keyboard.append([InlineKeyboardButton("Cancellarmi da UberNEST", callback_data=ccd("ME", "USER_REMOVAL"))])
    keyboard.append([InlineKeyboardButton("Uscire", callback_data=ccd("EXIT"))])
    return InlineKeyboardMarkup(keyboard)


def trips_keyboard(chat_id):
    keyboard = [[InlineKeyboardButton("Aggiungi un nuovo viaggio",
                                      callback_data=ccd("TRIPS", "NEW_TRIP"))]]

    for day in common.work_days:
        for direction in secret_data.groups:
            time = common.get_trip_time(chat_id, day, direction)
            if time is not None:
                group = secret_data.groups[direction][day][chat_id]
                occupied_slots = len(group["Permanent"]) + len(group["Temporary"])
                keyboard.append(
                    [InlineKeyboardButton(day + ": " + time + " " + common.direction_to_name(direction)
                                          + " (" + str(occupied_slots) + ")",
                                          callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))])

    keyboard.append([InlineKeyboardButton("Indietro", callback_data=ccd("ME_MENU"))])
    keyboard.append([InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))])
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
                        callback_data=ccd(
                            "BOOKING", direction, day, driver, mode))])
            except TypeError:
                log.debug("No bookings found")

    keyboard.append([InlineKeyboardButton("Indietro", callback_data=ccd("BOOKING", mode))])
    keyboard.append([InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))])
    return InlineKeyboardMarkup(keyboard)
