# -*- coding: utf-8 -*-
import datetime

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup

import logging as log
import common
import secrets
from common import today, tomorrow, get_partenza
from inline import separate_callback_data, create_callback_data


# Comando iniziale che viene chiamato dall'utente
def prenota(bot, update):
    keyboard = []
    keyboard.append([InlineKeyboardButton("Prenotare una-tantum",
                                          callback_data=create_callback_data("SINGLEBOOKING", []))])
    keyboard.append([InlineKeyboardButton("Prenotare in maniera permanente",
                                          callback_data=create_callback_data("BOOKING", [None]))])
    keyboard.append([InlineKeyboardButton("Disdire una prenotazione",
                                          callback_data=create_callback_data("DELETEBOOKING", []))])
    bot.send_message(chat_id=update.message.chat_id,
                     text="Cosa vuoi fare?",
                     reply_markup=InlineKeyboardMarkup(keyboard))


# Funzione per prelevare le prenotazioni da secrets
def fetch_bookings(bot, update, date):
    if (date == today() and common.is_today_weekday()) or (date == tomorrow() and common.is_tomorrow_weekday()):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Lista delle prenotazioni per "
                              + date.lower() + ": ")

        groups = secrets.groups_morning[date]
        if len(groups) > 0:
            message = "Persone in salita: \n\n"
            for i in groups:
                people = [secrets.users[k] for i in groups for k in groups[i]]
                bot.send_message(chat_id=update.message.chat_id,
                                 text=message + secrets.users[i] + ":\n" + ", ".join(people))

        groups = secrets.groups_evening[date]
        if len(groups) > 0:
            message = "Persone in discesa: \n\n"
            for i in groups:
                people = [secrets.users[k] for i in groups for k in groups[i]]
                bot.send_message(chat_id=update.message.chat_id,
                                 text=message + secrets.users[i] + ":\n" + ", ".join(people))

    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text=date + " UberNEST non sarà attivo.")


# Funzione chiamata in seguito alla risposta dell'utente
def booking_handler(bot, update):
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()
    if separate_callback_data(update.callback_query.data)[1] == "None":
        time = (datetime.datetime.now() + datetime.timedelta(hours=1 + common.is_dst())).time()
        if datetime.time(6, 0) <= time <= datetime.time(20, 0) and common.is_tomorrow_weekday():
            bot.send_message(chat_id=chat_id,
                             text="Scegli una persona:",
                             reply_markup=persone_keyboard(tomorrow()))
        else:
            bot.send_message(chat_id=chat_id,
                             text="Mi dispiace, è possibile effettuare prenotazioni"
                                  " tramite il bot solo dalle 6:00 alle 20:00 del giorno"
                                  " prima. Inoltre, UberNEST è attivo dal Lunedì al Venerdì.")
    else:
        person, direction = separate_callback_data(update.callback_query.data)[1:]
        person = str(person).decode('utf-8')

        try:
            if direction == "Salita":
                groups = secrets.groups_morning[tomorrow()]
            elif direction == "Discesa":
                groups = secrets.groups_evening[tomorrow()]
            else:
                groups = None
        except KeyError as ex:
            groups = None

        if len(groups[person]) < 4:
            if str(chat_id).decode('utf-8') == person:
                bot.send_message(chat_id=chat_id, text="Sei tu l'autista!")
            elif str(chat_id).decode('utf-8') not in groups[person]:
                bot.send_message(chat_id=chat_id, text="Prenotato con "
                                                       + secrets.users[person] + " per domani con successo.")
                groups[person].append(str(chat_id).decode('utf-8'))
            else:
                bot.send_message(chat_id=chat_id, text="Ti sei già prenotato per domani con questa persona!")
        else:
            bot.send_message(chat_id=chat_id, text="Posti per domani esauriti.")


# Keyboard customizzata per visualizzare le prenotazioni in maniera inline
# Day è un oggetto di tipo stringa
def persone_keyboard(day):
    keyboard = []
    for i in secrets.groups_morning[day]:
        try:
            keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + get_partenza(i, day, "Salita"),
                                                  callback_data=create_callback_data("BOOKING", [i, "Salita"]))])
        except TypeError as ex:
            log.info("No bookings found")
    for i in secrets.groups_evening[day]:
        try:
            keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + get_partenza(i, day, "Discesa"),
                                                  callback_data=create_callback_data("BOOKING", [i, "Discesa"]))])
        except TypeError as ex:
            log.info("No bookings found")
    return InlineKeyboardMarkup(keyboard)
