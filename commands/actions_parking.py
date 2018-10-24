# -*- coding: utf-8 -*-

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import secrets
from util import common
from util.filters import create_callback_data as ccd, separate_callback_data


def parcheggio(bot, update):
    chat_id = str(update.message.chat_id)

    # Controllo per evitare che i non autisti usino il comando
    if chat_id not in secrets.drivers:
        return

    keyboard = [
        [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
    ]

    day = common.today()
    trip = secrets.groups["Discesa"][day]

    if common.is_weekday(day):
        if chat_id in trip and not trip[chat_id]["Suspended"]:
            for item in common.locations:
                keyboard.insert(0, [InlineKeyboardButton(item, callback_data=ccd("CONFIRM_PARK", item))])

            if "Location" in trip[chat_id]:
                message = f"La posizione di ritrovo corrente è settata a: {trip[chat_id]['Location']}." \
                          f"\nSeleziona un nuovo luogo di ritrovo."
            else:
                message = "Seleziona il luogo di ritrovo per il viaggio di ritorno."
        else:
            message = "Mi dispiace, non sembra che tu abbia viaggi in programma da Povo verso il NEST oggi." \
                      " Inseriscine uno e riprova.",
    else:
        message = "Mi dispiace, è possibile selezionare il luogo di parcheggio nei giorni in cui UberNEST è attivo.",

    bot.send_message(chat_id=chat_id, text=message, reply_markup=InlineKeyboardMarkup(keyboard))


def confirm_parking(bot, update):
    chat_id = str(update.callback_query.message.chat_id)
    data = separate_callback_data(update.callback_query.data)

    location = data[2]

    keyboard = [
        [InlineKeyboardButton("📍 Mostra sulla mappa", callback_data=("SEND_LOCATION", location))],
        [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
    ]

    day_group = secrets.groups["Discesa"][common.today()][chat_id]
    day_group["Location"] = location

    bot.edit_message_text(chat_id=chat_id,
                          message_id=update.callback_query.message.message_id,
                          text=f"Posizione impostata con successo: {location}",
                          reply_markup=InlineKeyboardMarkup(keyboard))

    for passenger_group in day_group["Temporary"], day_group["Permanent"]:
        for passenger in passenger_group:
            bot.send_message(chat_id=passenger,
                             text=f"Per il viaggio di ritorno,"
                                  f" [{secrets.users[chat_id]['Name']}](tg://user?id={chat_id})"
                                  f" ha impostato il luogo di ritrovo:\n📍 {location}.",
                             reply_markup=InlineKeyboardMarkup(keyboard))


def send_location(bot, update):
    chat_id = str(update.callback_query.message.chat_id)
    data = separate_callback_data(update.callback_query.data)

    location = data[2]

    latitude, longitude = common.locations[location]["Location"]

    bot.send_location(chat_id=chat_id, latitude=latitude, longitude=longitude)
