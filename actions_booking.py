# -*- coding: utf-8 -*-

import datetime
import logging as log
import common
import secrets
import inline

from common import tomorrow, get_partenza
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup


# Comando iniziale che viene chiamato dall'utente
def prenota(bot, update):
    if str(update.message.chat_id) in secrets.users:
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

        trips = secrets.groups[direction][tomorrow()][driver]

        if len(trips["Permanent"]) + len(trips["Temporary"]) < secrets.drivers[driver][u"Slots"]:
            if str(chat_id) == driver:
                bot.send_message(chat_id=chat_id, text="Sei tu l'autista!")
            elif str(chat_id) not in trips["Temporary"] and str(chat_id) not in trips["Permanent"]:
                trips[mode].append(str(chat_id))
                bot.send_message(chat_id=chat_id, text="Prenotazione completata. Dati del viaggio:"
                                                       + "\n\nAutista: " + secrets.users[driver][u"Name"]
                                                       + "\nGiorno: " + day
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
        bookings = common.search_by_booking(str(chat_id))
        if len(bookings) > 0:
            keyboard = []
            for i in bookings:
                direction, day, driver, mode = i

                keyboard.append(
                    [InlineKeyboardButton(common.localize_direction(mode) + " il " + day
                                          + " con " + secrets.users[driver][u"Name"] + " - " +
                                          get_partenza(driver, day, direction),
                                          callback_data=inline.create_callback_data("DELETEBOOKING", *i))])
            keyboard.append(
                [InlineKeyboardButton("Annulla",
                                      callback_data=inline.create_callback_data("CANCEL"))])
            bot.send_message(chat_id=chat_id, text="Clicca su una prenotazione per cancellarla.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            bot.send_message(chat_id=chat_id, text="Mi dispiace, ma non hai prenotazioni all'attivo.")
    elif len(data) == 5:
        keyboard = []
        data[0] = "CONFIRM"

        keyboard.append(InlineKeyboardButton(
            "Sì", callback_data=inline.create_callback_data("DELETEBOOKING", *data)))  # len == 6
        keyboard.append(InlineKeyboardButton(
            "No", callback_data=inline.create_callback_data("CANCEL")))

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif len(data) == 6:
        direction, day, driver, mode = data[2:]
        secrets.groups[direction][day][driver][mode].remove(str(chat_id))
        bot.send_message(chat_id=chat_id, text="Prenotazione cancellata con successo.")


# Keyboard customizzata per visualizzare le prenotazioni in maniera inline
# Day è un oggetto di tipo stringa
def booking_keyboard(mode, day):
    keyboard = []

    for direction in secrets.groups:
        for driver in secrets.groups[direction][day]:
            try:
                keyboard.append(
                    [InlineKeyboardButton(secrets.users[driver][u"Name"] + " - " + get_partenza(driver, day, direction),
                                          callback_data=inline.create_callback_data(
                                              "BOOKING", direction, day, driver, mode))])
            except TypeError:
                log.info("No bookings found")

    keyboard.append([InlineKeyboardButton("Annulla", callback_data=inline.create_callback_data("CANCEL"))])
    return InlineKeyboardMarkup(keyboard)
