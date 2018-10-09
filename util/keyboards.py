# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
        keyboard.append([InlineKeyboardButton("Modificare il numero di posti", callback_data=ccd("ME", "ED_DR_SL"))])
    else:
        money_string = "Gestire i miei debiti"
        driver_string = "Diventare un autista"

    keyboard.append([InlineKeyboardButton(money_string, callback_data=ccd("MONEY"))])
    keyboard.append([InlineKeyboardButton(driver_string, callback_data=ccd("ME", "DRIVER"))])
    keyboard.append([InlineKeyboardButton("Cancellarmi da UberNEST", callback_data=ccd("ME", "US_RE"))])
    keyboard.append([InlineKeyboardButton("Uscire", callback_data=ccd("EXIT"))])

    return InlineKeyboardMarkup(keyboard)


def trips_keyboard(chat_id):
    keyboard = [[InlineKeyboardButton("Aggiungi un nuovo viaggio", callback_data=ccd("TRIPS", "NEW_TRIP"))]]

    for day in common.work_days:
        for direction in "Salita", "Discesa":
            try:
                group = secret_data.groups[direction][day][chat_id]

                if group["Suspended"]:
                    counter = "SOSP."
                else:
                    counter = len(group["Permanent"]) + len(group["Temporary"])

                keyboard.append(
                    [InlineKeyboardButton(day + ": " + group["Time"] + " " + common.direction_to_name(direction)
                                          + " (" + str(counter) + ")",
                                          callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))])
            except KeyError:
                continue

    keyboard.append([InlineKeyboardButton("Indietro", callback_data=ccd("ME_MENU"))])
    keyboard.append([InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))])

    return InlineKeyboardMarkup(keyboard)


# Keyboard customizzata per visualizzare le prenotazioni in maniera inline
# Day è un oggetto di tipo stringa

def booking_keyboard(mode, day, from_booking):
    keyboard = []

    bookings = sorted(
        [
            # Restituisce una tupla del tipo (ora, guidatore, direzione, chat_id) riordinata
            (secret_data.groups[direction][day][driver]["Time"],
             secret_data.users[driver]["Name"], direction, driver)

            for direction in secret_data.groups
            for driver in secret_data.groups[direction][day]
        ]
    )

    for time, name, direction, driver in bookings:
        if not secret_data.groups[direction][day][driver]["Suspended"]:
            keyboard.append(
                [InlineKeyboardButton("🚗 " + name + " - 🕓 " + time + "\n➡ " + common.direction_to_name(direction),
                                      callback_data=ccd("BOOKING", "CONFIRM", direction, day, driver, mode))])

    keyboard.append([InlineKeyboardButton("Vai alla selezione giorno", callback_data=ccd("BOOKING", "NEW", mode))])
    keyboard.append([InlineKeyboardButton("Vai a /" + day[:-1].lower() + "i", callback_data=ccd("SHOW_BOOKINGS", day))])
    keyboard.append([InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))])

    return InlineKeyboardMarkup(keyboard)
