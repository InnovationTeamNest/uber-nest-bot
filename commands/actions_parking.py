# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging as log

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest

import secret_data
from util import common
from util.filters import create_callback_data as ccd, separate_callback_data


def parcheggio(bot, update):
    if update.callback_query:
        chat_id = str(update.callback_query.from_user.id)
        try:
            update.callback_query.message.delete()
        except BadRequest:
            log.info("Failed to delete previous message")
        data = separate_callback_data(update.callback_query.data)
        action = data[1]
    else:
        chat_id = str(update.message.chat_id)
        data = None
        action = "CHOOSE"

    # Controllo per evitare che i non autisti usino il comando
    if chat_id not in secret_data.drivers:
        return

    keyboard = [
        [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
    ]

    if action == "CHOOSE":
        if common.is_weekday(common.today()):
            if chat_id in secret_data.groups["Discesa"][common.today()]:
                for item in common.locations:
                    keyboard.insert(0, [InlineKeyboardButton(item, callback_data=ccd("PARK", "SET", item))])

                bot.send_message(chat_id=chat_id, text="Seleziona il luogo di ritrovo per il viaggio di ritorno. ",
                                 reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                bot.send_message(chat_id=chat_id, text="Mi dispiace, non sembra che tu abbia viaggi in programma"
                                                       " da Povo verso il NEST oggi. Inseriscine uno e riprova.",
                                 reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            bot.send_message(chat_id=chat_id, text="Mi dispiace, è possibile selezionare il luogo"
                                                   " di parcheggio nei giorni in cui UberNEST è attivo.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "SET":
        location = data[2]
        day_group = secret_data.groups["Discesa"][common.today()][chat_id]
        day_group["Location"] = location

        bot.send_message(chat_id=chat_id, text="Posizione impostata con successo: " + location,
                         reply_markup=InlineKeyboardMarkup(keyboard))

        for passenger_group in day_group["Temporary"], day_group["Permanent"]:
            for passenger in passenger_group:
                bot.send_message(chat_id=passenger, text="Per il viaggio di ritorno, "
                                                         + secret_data.users[chat_id]["Name"]
                                                         + " ha impostato il luogo di ritrovo:\n"
                                                         + "📍 " + location + ".")
