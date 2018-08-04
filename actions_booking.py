# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import logging as log
import common
import inline

from common import tomorrow, get_partenza
from secret_data import groups, drivers, users
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup


# Comando iniziale che viene chiamato dall'utente
def prenota(bot, update):
    if str(update.message.chat_id) in users:
        keyboard = [[InlineKeyboardButton("Prenotare una-tantum (solo per il giorno dopo)",
                                          callback_data=inline.create_callback_data("BOOKING", "Temporary"))],
                    [InlineKeyboardButton("Prenotare in maniera permanente",
                                          callback_data=inline.create_callback_data("BOOKING", "Permanent"))],
                    [InlineKeyboardButton("Visualizza e disdici una prenotazione",
                                          callback_data=inline.create_callback_data("DELETEBOOKING"))],
                    [InlineKeyboardButton("Esci dal menu",
                                          callback_data=inline.create_callback_data("CANCEL"))]]
        bot.send_message(chat_id=update.message.chat_id,
                         text="Cosa vuoi fare?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Per effettuare una prenotazione, registrati con /registra.")


# Funzione chiamata in seguito alla risposta dell'utente
def booking_handler(bot, update):
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    data = inline.separate_callback_data(update.callback_query.data)

    if len(data) == 2:  # Caso in cui è stato appena selezionato il bottone dal menu
        mode = data[1]
        if mode == "Temporary":
            if common.booking_time():
                bot.send_message(chat_id=chat_id,
                                 text="Viaggi disponibili per " + tomorrow().lower(),
                                 reply_markup=booking_keyboard(mode, tomorrow()))
            else:
                bot.send_message(chat_id=chat_id,
                                 text="Mi dispiace, è possibile effettuare prenotazioni"
                                      " tramite il bot solo dalle 6:00 alle 20:00 del giorno"
                                      " prima. Inoltre, UberNEST è attivo dal Lunedì al Venerdì.")
        elif mode == "Permanent":
            keyboard = []
            for i in range(0, 5, 1):
                if i != datetime.datetime.today().weekday():
                    keyboard.append(InlineKeyboardButton(
                        common.day_to_string(i)[:2],  # Abbreviazione del giorno
                        callback_data=inline.create_callback_data("BOOKING", mode, common.day_to_string(i))))
            bot.send_message(chat_id=chat_id, text="Scegli la data della prenotazione.",
                             reply_markup=InlineKeyboardMarkup([keyboard, [InlineKeyboardButton(
                                 "Annulla", callback_data=inline.create_callback_data("CANCEL"))]]))
    elif len(data) == 3:  # Caso in cui il trip sarà Permanent
        mode, day = data[1:3]
        if mode == "Permanent":
            bot.send_message(chat_id=chat_id, text="Viaggi disponibili per " + day.lower(),
                             reply_markup=booking_keyboard(mode, day))
    else:  # Caso in cui il trip sarà Temporaneo
        direction, day, driver, mode = data[1:]

        trips = groups[direction][day][driver]

        if len(trips["Permanent"]) + len(trips["Temporary"]) < drivers[driver]["Slots"]:
            if str(chat_id) == driver:
                bot.send_message(chat_id=chat_id, text="Sei tu l'autista!")
            elif str(chat_id) not in trips["Temporary"] and str(chat_id) not in trips["Permanent"]:
                trips[mode].append(str(chat_id))
                bot.send_message(chat_id=chat_id, text="Prenotazione completata. Dati del viaggio:"
                                                       + "\n\nAutista: " + str(users[driver]["Name"])
                                                       + "\nGiorno: " + str(day)
                                                       + "\nDirezione: " + common.direction_to_name(direction)
                                                       + "\nModalità: " + common.localize_direction(mode))
            else:
                bot.send_message(chat_id=chat_id, text="Ti sei già prenotato in questa data con questa persona!")
        else:
            bot.send_message(chat_id=chat_id, text="Posti in questa data esauriti.")


def delete_booking(bot, update):
    chat_id = update.callback_query.from_user.id
    data = inline.separate_callback_data(update.callback_query.data)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    if len(data) == 1:
        bookings = common.search_by_booking(str(chat_id), include_today=False)
        if len(bookings) > 0:
            keyboard = []
            for item in bookings:
                direction, day, driver, mode = item

                keyboard.append([
                    InlineKeyboardButton(common.localize_direction(mode) + " il " + day + " con " +
                                         users[driver]["Name"] + " - " + get_partenza(driver, day, direction),
                                         callback_data=inline.create_callback_data("DELETEBOOKING", *item))])
            keyboard.append(
                [InlineKeyboardButton("Annulla",
                                      callback_data=inline.create_callback_data("CANCEL"))])
            bot.send_message(chat_id=chat_id, text="Clicca su una prenotazione per cancellarla. Ricorda che non è "
                                                   "possibile cancellare le prenotazioni in data odierna.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            bot.send_message(chat_id=chat_id, text="Mi dispiace, ma non hai prenotazioni all'attivo.")
    elif len(data) == 5:
        data[0] = "CONFIRM"
        keyboard = [InlineKeyboardButton("Sì", callback_data=inline.create_callback_data("DELETEBOOKING", *data)),
                    InlineKeyboardButton("No", callback_data=inline.create_callback_data("CANCEL"))]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif len(data) == 6:
        direction, day, driver, mode = data[2:]
        groups[direction][day][driver][mode].remove(str(chat_id))
        bot.send_message(chat_id=chat_id, text="Prenotazione cancellata con successo.")


# Keyboard customizzata per visualizzare le prenotazioni in maniera inline
# Day è un oggetto di tipo stringa
def booking_keyboard(mode, day):
    keyboard = []

    for direction in groups:
        for driver in groups[direction][day]:
            try:
                keyboard.append(
                    [InlineKeyboardButton(users[driver]["Name"] + " - " + get_partenza(driver, day, direction),
                                          callback_data=inline.create_callback_data(
                                              "BOOKING", direction, day, driver, mode))])
            except TypeError:
                log.debug("No bookings found")

    keyboard.append([InlineKeyboardButton("Annulla", callback_data=inline.create_callback_data("CANCEL"))])
    return InlineKeyboardMarkup(keyboard)
