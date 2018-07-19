# -*- coding: utf-8 -*-

import datetime
import logging as log
import common
import secrets

from common import tomorrow, get_partenza
from inline import separate_callback_data, create_callback_data
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup


# Comando iniziale che viene chiamato dall'utente
def prenota(bot, update):
    if str(update.message.chat_id).decode('utf-8') in secrets.users:
        keyboard = []
        keyboard.append([InlineKeyboardButton("Prenotare una-tantum",
                                              callback_data=create_callback_data("BOOKING", ["Temporary"]))])
        keyboard.append([InlineKeyboardButton("Prenotare in maniera permanente",
                                              callback_data=create_callback_data("BOOKING", ["Permanent"]))])
        keyboard.append([InlineKeyboardButton("Visualizza e disdici una prenotazione",
                                              callback_data=create_callback_data("DELETEBOOKING", []))])
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

    data = separate_callback_data(update.callback_query.data)
    mode = data[1]

    log.info("Mode:" + str(mode) + ", length: " + str(len(data)))

    if len(data) == 2 and (mode == "Permanent" or mode == "Temporary"):
        time = (datetime.datetime.now() + datetime.timedelta(hours=1 + common.is_dst())).time()
        if datetime.time(6, 0) <= time <= datetime.time(20, 0) and common.is_weekday(tomorrow()):
            bot.send_message(chat_id=chat_id,
                             text="Scegli una persona:",
                             reply_markup=booking_keyboard(mode, tomorrow()))
        else:
            bot.send_message(chat_id=chat_id,
                             text="Mi dispiace, è possibile effettuare prenotazioni"
                                  " tramite il bot solo dalle 6:00 alle 20:00 del giorno"
                                  " prima. Inoltre, UberNEST è attivo dal Lunedì al Venerdì.")
    elif (mode == "Permanent" or mode == "Temporary"):
        person, direction = data[2:]
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

        booker = str(chat_id).decode('utf-8')
        if len(groups[person]["Permanent"]) + len(groups[person]["Temporary"]) < 4:
            if booker == person:
                bot.send_message(chat_id=chat_id, text="Sei tu l'autista!")
            elif booker not in groups[person]["Temporary"] and \
                    booker not in groups[person]["Permanent"]:
                bot.send_message(chat_id=chat_id, text="Prenotato con "
                                                       + secrets.users[person] + " per domani con successo.")
                groups[person][mode].append(booker)
            else:
                bot.send_message(chat_id=chat_id, text="Ti sei già prenotato per domani con questa persona!")
        else:
            bot.send_message(chat_id=chat_id, text="Posti per domani esauriti.")


def deletebooking_handler(bot, update):
    chat_id = update.callback_query.from_user.id
    data = separate_callback_data(update.callback_query.data)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    log.info("Length: " + str(len(data)))

    if len(data) == 1:
        bookings = common.search_by_booking(str(chat_id))
        if len(bookings) > 0:
            keyboard = []
            for i in bookings:
                direction, day, driver, mode = i
                if mode == "Temporary":
                    keyboard.append(
                        [InlineKeyboardButton("Temporanea il " + day + " con " + secrets.users[driver] + " - " +
                                              get_partenza(driver, day, direction),
                                              callback_data=create_callback_data("DELETEBOOKING", i))])
                elif mode == "Permanent":
                    keyboard.append(
                        [InlineKeyboardButton("Permanente il " + day + " con " + secrets.users[driver] + " - " +
                                              get_partenza(driver, day, direction),
                                              callback_data=create_callback_data("DELETEBOOKING", i))])
            keyboard.append(
                [InlineKeyboardButton("Annulla", callback_data=create_callback_data("DELETEBOOKING", ["CANCEL"]))])
            bot.send_message(chat_id=chat_id, text="Clicca su una prenotazione per cancellarla.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            bot.send_message(chat_id=chat_id, text="Mi dispiace, ma non hai prenotazioni all'attivo.")
    elif len(data) == 2 and data[1] == "CANCEL":
        bot.send_message(chat_id=chat_id, text="Operazione annullata")
    elif len(data) == 5:
        keyboard = []
        data[0] = "CONFIRM"
        keyboard.append(InlineKeyboardButton(
            "Sì", callback_data=create_callback_data("DELETEBOOKING", data)))
        keyboard.append(InlineKeyboardButton(
            "No", callback_data=create_callback_data("DELETEBOOKING", ["CANCEL"])))
        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif len(data) == 6:
        direction, day, driver, mode = data[2:]
        if direction == "Salita":
            secrets.groups_morning[day][driver][mode].remove(str(chat_id))
        elif direction == "Discesa":
            secrets.groups_evening[day][driver][mode].remove(str(chat_id))
        bot.send_message(chat_id=chat_id, text="Prenotazione cancellata con successo.")


# Keyboard customizzata per visualizzare le prenotazioni in maniera inline
# Day è un oggetto di tipo stringa
def booking_keyboard(mode, day):
    keyboard = []
    for i in secrets.groups_morning[day]:
        try:
            keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + get_partenza(i, day, "Salita"),
                                                  callback_data=create_callback_data("BOOKING", [mode, i, "Salita"]))])
        except TypeError as ex:
            log.info("No bookings found")
    for i in secrets.groups_evening[day]:
        try:
            keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + get_partenza(i, day, "Discesa"),
                                                  callback_data=create_callback_data("BOOKING", [mode, i, "Discesa"]))])
        except TypeError as ex:
            log.info("No bookings found")
    return InlineKeyboardMarkup(keyboard)
