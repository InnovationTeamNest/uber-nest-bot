# -*- coding: utf-8 -*-
import sys

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest

import secrets
from util import common
from util.filters import create_callback_data as ccd, separate_callback_data


def parcheggio(bot, update):
    if update.callback_query:
        chat_id = str(update.callback_query.from_user.id)
        try:
            update.callback_query.message.delete()
        except BadRequest:
            print("Failed to delete previous message", file=sys.stderr)
        data = separate_callback_data(update.callback_query.data)
        action = data[1]
    else:
        chat_id = str(update.message.chat_id)
        data = None
        action = "CHOOSE"

    # Controllo per evitare che i non autisti usino il comando
    if chat_id not in secrets.drivers:
        return

    keyboard = [
        [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
    ]

    if action == "CHOOSE":
        day = common.today()
        if common.is_weekday(day):
            if chat_id in secrets.groups["Discesa"][day] and not \
                    secrets.groups["Discesa"][day][chat_id]["Suspended"]:
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
        day_group = secrets.groups["Discesa"][common.today()][chat_id]
        user_name = secrets.users[chat_id]["Name"]
        day_group["Location"] = location

        bot.send_message(chat_id=chat_id, text="Posizione impostata con successo: " + location,
                         reply_markup=InlineKeyboardMarkup(keyboard))

        for passenger_group in day_group["Temporary"], day_group["Permanent"]:
            for passenger in passenger_group:
                bot.send_message(chat_id=passenger, text=f"Per il viaggio di ritorno, {user_name}"
                                                         f" ha impostato il luogo di ritrovo:\n📍 {location}.")
