# -*- coding: utf-8 -*-

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import secrets
from util import common
from util.filters import create_callback_data as ccd


#
# Tastiera chiamata dal menù /me. Cambia a seconda che il guidatore è un autista o meno.
#
def me_keyboard(chat_id):
    keyboard = []
    if chat_id in secrets.drivers:
        money_string = "💰 Gestire i miei debiti e crediti"
        driver_string = "🚫 Smettere di essere un autista"
        keyboard.append([InlineKeyboardButton("🚗 Gestire i miei viaggi", callback_data=ccd("ME", "TRIPS"))])
        keyboard.append([InlineKeyboardButton(f"{common.emoji_numbers[secrets.drivers[chat_id]['Slots']]}"
                                              f" Modificare il numero di posti", callback_data=ccd("ME", "ED_DR_SL"))])
    else:
        money_string = "💸 Gestire i miei debiti"
        driver_string = "🚗 Diventare un autista"

    keyboard.append([InlineKeyboardButton(money_string, callback_data=ccd("MONEY"))])
    keyboard.append([InlineKeyboardButton(driver_string, callback_data=ccd("ME", "DRIVER"))])
    keyboard.append([InlineKeyboardButton("❌ Cancellarmi da UberNEST", callback_data=ccd("ME", "US_RE"))])
    keyboard.append([InlineKeyboardButton("🔚 Uscire", callback_data=ccd("EXIT"))])

    return InlineKeyboardMarkup(keyboard)


#
# Tastiera chiamata dal menù TRIPS di /me. Mostra tutti i viaggi di un certo autista, inclusi i posti liberi
# oppure SOSP se il viaggio risulta sospeso.
#
def trips_keyboard(chat_id):
    keyboard = [[InlineKeyboardButton("Aggiungi un nuovo viaggio", callback_data=ccd("TRIPS", "ADD"))]]

    for day in common.work_days:
        for direction in "Salita", "Discesa":
            try:
                group = secrets.groups[direction][day][chat_id]

                if group["Suspended"]:
                    counter = "SOSP."
                else:
                    counter = str(len(group["Permanent"]) + len(group["Temporary"]))

                keyboard.append(
                    [InlineKeyboardButton(f"{day}: {group['Time']}"
                                          f" {common.dir_name(direction)} ({counter})",
                                          callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))])
            except KeyError:
                continue

    keyboard.append([InlineKeyboardButton("↩ Indietro", callback_data=ccd("ME_MENU"))])
    keyboard.append([InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))])

    return InlineKeyboardMarkup(keyboard)


#
# Tastiera chiamata con i menù di /prenota. mode e day sono due oggetti di tipo /prenota.
# Al suo interno non vengono mai visualizzati i viaggi sospesi.
# Vi sono inoltre due bottoni per cambiare liberamente tra la visualizzazione prenotzione e la
# visualizzazione giorno semplice.
#
def booking_keyboard(mode, day):
    keyboard = []

    bookings = sorted(
        [
            # Restituisce una tupla del tipo (ora, guidatore, direzione, chat_id) riordinata
            (secrets.groups[direction][day][driver]["Time"],
             secrets.users[driver]["Name"], direction, driver)

            for direction in secrets.groups
            for driver in secrets.groups[direction][day]
        ]
    )

    for time, name, direction, driver in bookings:
        if not secrets.groups[direction][day][driver]["Suspended"]:
            keyboard.append(
                [InlineKeyboardButton(f"🚗 {name.split(' ')[-1]} 🕓 {time} "
                                      f"{common.dir_name(direction)}",
                                      callback_data=ccd("BOOKING", "CONFIRM", direction, day, driver, mode))])

    keyboard.append([InlineKeyboardButton("Vai alla selezione giorno", callback_data=ccd("BOOKING", "NEW", mode))])
    keyboard.append([InlineKeyboardButton(f"Vai a /{day[:-1].lower()}ì", callback_data=ccd("SHOW_BOOKINGS", day))])
    keyboard.append([InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))])

    return InlineKeyboardMarkup(keyboard)
