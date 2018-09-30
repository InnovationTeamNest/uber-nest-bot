# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import logging as log

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import secret_data
import util.common as common
from util.filters import create_callback_data as ccd, separate_callback_data
from util.keyboards import booking_keyboard


# Comando iniziale che viene chiamato dall'utente

def prenota(bot, update):
    if update.callback_query:
        chat_id = update.callback_query.from_user.id
        try:
            update.callback_query.message.delete()
        except BadRequest:
            log.info("Failed to delete previous message")
    else:
        chat_id = update.message.chat_id

    if str(chat_id) in secret_data.users:
        keyboard = [[InlineKeyboardButton("Prenotare una-tantum",
                                          callback_data=ccd("BOOKING", "NEW", "Temporary"))],
                    [InlineKeyboardButton("Prenotare in maniera permanente",
                                          callback_data=ccd("BOOKING", "NEW", "Permanent"))],
                    [InlineKeyboardButton("Gestire le mie prenotazioni",
                                          callback_data=ccd("DELETE_BOOKING", "LIST"))],
                    [InlineKeyboardButton("Uscire", callback_data=ccd("EXIT"))]]
        bot.send_message(chat_id=chat_id,
                         text="Cosa vuoi fare?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        bot.send_message(chat_id=chat_id,
                         text="Per effettuare una prenotazione, registrati con /registra.")


def booking_handler(bot, update):
    data = separate_callback_data(update.callback_query.data)
    action = data[1]
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    if action == "NEW":  # Dati in entrata ("BOOKING", "NEW", mode)
        if common.booking_time():
            text = ""
            mode = data[2]

            if mode == "Temporary":
                text = text + "Si ricorda che le prenotazioni una-tantum vengono automaticamente cancellate ed" \
                       + " addebitate il giorno dopo la prenotazione. E' possibile prenotarsi a un viaggio" \
                       + " già avvenuto, ma verrà addebitato comunque."
            elif mode == "Permanent":
                text = text + "Si ricorda che le prenotazioni permanenti verranno addebitate anche per i viaggi" \
                       + " prenotati per la giornata corrente."

            keyboard = []
            for day in common.work_days:
                keyboard.append(InlineKeyboardButton(day[:2],  # Abbreviazione del giorno
                                                     callback_data=ccd("BOOKING", "DAY", mode, day)))

            keyboard = [
                keyboard,
                [InlineKeyboardButton("Indietro", callback_data=ccd("BOOKING_MENU"))],
                [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
            ]

            bot.send_message(chat_id=chat_id, text=text + "\n\nScegli la data della prenotazione.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            bot.send_message(chat_id=chat_id,
                             text="Mi dispiace, è possibile effettuare prenotazioni"
                                  + " tramite UberNEST solo dalle "
                                  + common.booking_start.strftime("%H:%M") + " alle "
                                  + common.booking_end.strftime("%H:%M") + ".")
    elif action == "DAY":  # Dati in entrata ("BOOKING", "DAY", mode, day)
        mode, day = data[2:4]
        bot.send_message(chat_id=chat_id, text="Viaggi disponibili per " + day.lower() + ":",
                         reply_markup=booking_keyboard(mode, day, from_booking=True))
    elif action == "DAY_CUSTOM":
        mode, day = data[2:4]
        bot.send_message(chat_id=chat_id, text="Viaggi disponibili per " + day.lower() + ":",
                         reply_markup=booking_keyboard(mode, day, from_booking=False))
    elif action == "CONFIRM":  # Dati in entrata ("BOOKING", "CONFIRM", direction, day, driver, mode)
        direction, day, driver, mode = data[2:]

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("BOOKING", "DAY", mode, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        trip = secret_data.groups[direction][day][driver]
        occupied_slots = len(trip["Permanent"]) + len(trip["Temporary"])
        total_slots = secret_data.drivers[driver]["Slots"]

        if str(chat_id) == driver:
            bot.send_message(chat_id=chat_id, text="Sei tu l'autista!",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        elif occupied_slots >= total_slots:
            bot.send_message(chat_id=chat_id, text="Macchina piena, vai a piedi LOL",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        elif str(chat_id) in trip["Temporary"] or str(chat_id) in trip["Permanent"]:
            bot.send_message(chat_id=chat_id, text="Ti sei già prenotato in questa data con questa persona!",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            trip[mode].append(str(chat_id))
            bot.send_message(chat_id=chat_id,
                             text="Prenotazione completata. Dati del viaggio:"
                                  + "\n\n🚗: " + str(secret_data.users[driver]["Name"])
                                  + "\n🗓: " + day
                                  + "\n🕓: " + trip["Time"]
                                  + "\n➡: " + common.direction_to_name(direction)
                                  + "\n🔁: " + common.localize_mode(mode),
                             reply_markup=InlineKeyboardMarkup(keyboard))
            bot.send_message(chat_id=driver,
                             text="Hai una nuova prenotazione " + common.localize_mode(mode).lower()
                                  + " da parte di " + secret_data.users[str(chat_id)]["Name"]
                                  + " per " + day + " " + common.direction_to_name(direction)
                                  + ". Posti rimanenti: " + str(total_slots - occupied_slots - 1))


def delete_booking(bot, update):
    chat_id = update.callback_query.from_user.id
    data = separate_callback_data(update.callback_query.data)
    action = data[1]

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    if action == "LIST":
        # Ricerca di tutte le prenotazioni legate all'utente
        bookings = common.search_by_booking(str(chat_id))

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("BOOKING_MENU"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        if len(bookings) > 0:
            user_keyboard = []

            for item in bookings:
                direction, day, driver, mode, time = item

                if day == common.today() and datetime.datetime.strptime(time, "%H:%M").hour > common.now_time().hour:
                    callback_data = ccd("DELETE_BOOKING", "DENIED_DELETION", driver)
                else:
                    callback_data = ccd("DELETE_BOOKING", "CONFIRM_DELETION", *item)

                # Aggiunta del bottone
                keyboard.append([InlineKeyboardButton(
                    "🚗 " + secret_data.users[driver]["Name"] + " - 🕓 " + day + " alle " + str(time)
                    + "\n➡ " + common.direction_to_name(direction) + " - " + common.localize_mode(mode),
                    callback_data=callback_data)])

            keyboard = user_keyboard + keyboard

            bot.send_message(chat_id=chat_id,
                             text="Clicca su una pregroup = secret_data.groups[direction][day][chat_id]notazione per modificarla o cancellarla.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            bot.send_message(chat_id=chat_id, text="Mi dispiace, ma non hai prenotazioni all'attivo.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "DENIED_DELETION":  # Caso in cui la cancellazione è stata negata
        driver = str(data[2])

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("DELETE_BOOKING", "LIST"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Mi dispiace, ma ormai è tardi per cancellare questa "
                              + "prenotazione. Rivolgiti direttamente a "
                              + secret_data.users[driver]["Name"],
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "CONFIRM_DELETION":
        booking = data[2:]

        keyboard = [
            InlineKeyboardButton("Sì", callback_data=ccd("DELETE_BOOKING", "SUCCESSFUL_DELETION", *booking)),
            InlineKeyboardButton("No", callback_data=ccd("DELETE_BOOKING", "LIST"))
        ]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup([keyboard]))

    elif action == "SUCCESSFUL_DELETION":  # Caso in cui la prenotazione è stata marchiata come cancellata
        direction, day, driver, mode, time = data[2:]
        secret_data.groups[direction][day][driver][mode].remove(str(chat_id))

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("DELETE_BOOKING", "LIST"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Prenotazione cancellata con successo.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
        bot.send_message(chat_id=driver,
                         text=secret_data.users[str(chat_id)]["Name"]
                              + " ha cancellato la prenotazione per " + day + " "
                              + common.direction_to_name(direction) + ".")
