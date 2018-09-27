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
        keyboard = [[InlineKeyboardButton("Prenotare una-tantum", callback_data=ccd("BOOKING", "Temporary"))],
                    [InlineKeyboardButton("Prenotare in maniera permanente",
                                          callback_data=ccd("BOOKING", "Permanent"))],
                    [InlineKeyboardButton("Gestire le mie prenotazioni", callback_data=ccd("DELETE_BOOKING"))],
                    [InlineKeyboardButton("Uscire", callback_data=ccd("EXIT"))]]
        bot.send_message(chat_id=chat_id,
                         text="Cosa vuoi fare?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        bot.send_message(chat_id=chat_id,
                         text="Per effettuare una prenotazione, registrati con /registra.")


# Funzione chiamata in seguito alla risposta dell'utente
def booking_handler(bot, update):
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    data = separate_callback_data(update.callback_query.data)

    if len(data) == 2:  # Caso in cui è stato appena selezionato il bottone dal menu
        mode = data[1]
        if common.booking_time():
            text = ""
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
                                                     callback_data=ccd("BOOKING", mode, day)))

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
    elif len(data) == 3:  # Scelta del giorno
        mode, day = data[1:3]
        bot.send_message(chat_id=chat_id, text="Viaggi disponibili per " + day.lower() + ":",
                         reply_markup=booking_keyboard(mode, day))
    else:  # Scelta del viaggio
        direction, day, driver, mode = data[1:]

        trip = secret_data.groups[direction][day][driver]
        occupied_slots = len(trip["Permanent"]) + len(trip["Temporary"])
        total_slots = secret_data.drivers[driver]["Slots"]

        if occupied_slots < total_slots:
            if str(chat_id) == driver:
                bot.send_message(chat_id=chat_id, text="Sei tu l'autista!")
            elif str(chat_id) not in trip["Temporary"] and str(chat_id) not in trip["Permanent"]:
                trip[mode].append(str(chat_id))
                bot.send_message(chat_id=chat_id,
                                 text="Prenotazione completata. Dati del viaggio:"
                                      + "\n\n🚗: " + str(secret_data.users[driver]["Name"])
                                      + "\n🗓: " + day
                                      + "\n🕓: " + trip["Time"]
                                      + "\n➡: " + common.direction_to_name(direction)
                                      + "\n🔁: " + common.localize_mode(mode))
                bot.send_message(chat_id=driver,
                                 text="Hai una nuova prenotazione " + common.localize_mode(mode).lower()
                                      + " da parte di " + secret_data.users[str(chat_id)]["Name"]
                                      + " per " + day + " " + common.direction_to_name(direction)
                                      + ". Posti rimanenti: " + str(total_slots - occupied_slots - 1))
            else:
                bot.send_message(chat_id=chat_id, text="Ti sei già prenotato in questa data con questa persona!")
        else:
            bot.send_message(chat_id=chat_id, text="Macchina piena, vai a piedi LOL")


def delete_booking(bot, update):
    chat_id = update.callback_query.from_user.id
    data = separate_callback_data(update.callback_query.data)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    if len(data) == 1:  # Caso iniziale
        bookings = common.search_by_booking(str(chat_id))
        if len(bookings) > 0:
            keyboard = []
            for item in bookings:
                direction, day, driver, mode = item
                # Ordine dei dati: DELETEBOOKING, direction, day, driver, mode
                time = common.get_trip_time(driver, day, direction)

                if day == common.today() and datetime.datetime.strptime(time, "%H:%M").hour > common.now_time().hour:
                    callback_data = ccd("DELETE_BOOKING", driver)
                else:
                    callback_data = ccd("DELETE_BOOKING", *item)
                # Aggiunta del bottone
                keyboard.append([InlineKeyboardButton(
                    common.localize_mode(mode) + " " + day + " con " + secret_data.users[driver]["Name"] + " - " + str(
                        time)
                    + " " + common.direction_to_name(direction), callback_data=callback_data)])

            keyboard.append([InlineKeyboardButton("Indietro", callback_data=ccd("BOOKING_MENU"))])
            keyboard.append([InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))])

            bot.send_message(chat_id=chat_id, text="Clicca su una prenotazione per modificarla o cancellarla.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [
                [InlineKeyboardButton("Indietro", callback_data=ccd("BOOKING_MENU"))],
                [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
            ]
            bot.send_message(chat_id=chat_id, text="Mi dispiace, ma non hai prenotazioni all'attivo.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 2:  # Caso in cui la cancellazione è stata negata
        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("BOOKING_MENU"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]
        bot.send_message(chat_id=chat_id,
                         text="Mi dispiace, ma ormai è tardi per cancellare questa "
                              + "prenotazione. Rivolgiti direttamente a "
                              + secret_data.users[str(data[1])]["Name"],
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 5:  # Caso in cui la prenotazione è stata selezionata
        data[0] = "CONFIRM"  # Ordine dei dati: DELETEBOOKING, CONFIRM, direction, day, driver, mode
        keyboard = [
            InlineKeyboardButton("Sì", callback_data=ccd("DELETE_BOOKING", *data)),
            InlineKeyboardButton("No", callback_data=ccd("BOOKING_MENU"))
        ]
        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif len(data) == 6:  # Caso in cui la prenotazione è stata marchiata come cancellata
        direction, day, driver, mode = data[2:]
        secret_data.groups[direction][day][driver][mode].remove(str(chat_id))
        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("BOOKING_MENU"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]
        bot.send_message(chat_id=chat_id, text="Prenotazione cancellata con successo.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
        bot.send_message(chat_id=driver,
                         text="L'utente " + secret_data.users[str(chat_id)]["Name"]
                              + " ha cancellato la prenotazione per " + day + " "
                              + common.direction_to_name(direction) + ".")
