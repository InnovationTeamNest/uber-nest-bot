# -*- coding: utf-8 -*-
import datetime

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup

import common
import secrets
from common import this_day, next_day, get_partenza
from inline import separate_callback_data, create_callback_data


# Comando iniziale che viene chiamato dall'utente
def prenota(bot, update):
    time = (datetime.datetime.now() + datetime.timedelta(hours=1 + common.is_dst())).time()
    if datetime.time(6, 0) <= time <= datetime.time(20, 0) and common.is_tomorrow_weekday():
        bot.send_message(chat_id=update.message.chat_id,
                         text="Scegli una persona:",
                         reply_markup=persone_keyboard())
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Mi dispiace, è possibile effettuare prenotazioni"
                              " tramite il bot solo dalle 6:00 alle 20:00 del giorno"
                              " prima. Inoltre, UberNEST è attivo dal Lunedì al Venerdì.")


# Funzione per prelevare le prenotazioni da secrets
def fetch_bookings(bot, update, date):
    if date == "Oggi":
        day = this_day()
    elif date == "Domani":
        day = next_day()
    else:
        day = None

    if (date == "Oggi" and common.is_today_weekday()) or (date == "Domani" and common.is_tomorrow_weekday()):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Lista delle prenotazioni per "
                              + date.lower() + " (" + str(day) + "): ")

        groups = secrets.groups_morning[day]
        if len(groups) > 0:
            message = "Persone in salita: \n\n"
            for i in groups:
                people = []
                for k in groups[i]:
                    people.append(secrets.users[k])
                bot.send_message(chat_id=update.message.chat_id,
                                 text=message + secrets.users[i] + ":\n" + ", ".join(people))

        groups = secrets.groups_evening[day]
        if len(groups) > 0:
            message = "Persone in discesa: \n\n"
            for i in groups:
                people = []
                for k in groups[i]:
                    people.append(secrets.users[k])
                bot.send_message(chat_id=update.message.chat_id,
                                 text=message + secrets.users[i] + ":\n" + ", ".join(people))

    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text=date + " UberNEST non sarà attivo.")


# Funzione chiamata in seguito alla risposta dell'utente
def booking_handler(bot, update):
    person, direction = separate_callback_data(update.callback_query.data)[1:]
    person = str(person).decode('utf-8')

    bot.send_chat_action(chat_id=update.callback_query.from_user.id,
                         action=ChatAction.TYPING)
    update.callback_query.message.delete()

    try:
        if direction == "Salita":
            groups = secrets.groups_morning[next_day()]
        elif direction == "Discesa":
            groups = secrets.groups_evening[next_day()]
        else:
            groups = None
    except KeyError as ex:
        groups = None

    if len(groups[person]) < 4:
        if str(update.callback_query.from_user.id).decode('utf-8') == person:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Sei tu l'autista!")
        elif str(update.callback_query.from_user.id).decode('utf-8') not in groups[person]:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Prenotato con " + secrets.users[person] + " per domani con successo.")
            groups[person].append(str(update.callback_query.from_user.id).decode('utf-8'))
        else:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Ti sei già prenotato per domani con questa persona!")
    else:
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text="Posti per domani esauriti.")


# Keyboard customizzata per visualizzare le prenotazioni in maniera inline
def persone_keyboard():
    keyboard = []
    for i in secrets.groups_morning[next_day()]:
        keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + get_partenza(i, "Salita"),
                                              callback_data=create_callback_data("BOOKING", [i, "Salita"]))])
    for i in secrets.groups_evening[next_day()]:
        keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + get_partenza(i, "Discesa"),
                                              callback_data=create_callback_data("BOOKING", [i, "Discesa"]))])
    return InlineKeyboardMarkup(keyboard)
