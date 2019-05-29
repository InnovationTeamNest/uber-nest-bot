# -*- coding: utf-8 -*-

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from data.data_api import is_driver, get_trip_group, get_trip, get_name
from routing.filters import create_callback_data as ccd, separate_callback_data
from util import common


def parcheggio(bot, update):
    chat_id = str(update.message.chat_id)

    # Controllo per evitare che i non autisti usino il comando
    if not is_driver(chat_id):
        return

    keyboard = [
        [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
    ]

    day = common.today()
    day_trips = get_trip_group("Discesa", day)

    if common.is_weekday(day):
        if chat_id in day_trips and not day_trips[chat_id]["Suspended"]:
            for location in common.locations:
                keyboard.insert(0, [InlineKeyboardButton(location, callback_data=ccd("CONFIRM_PARK", location))])

            if "Location" in day_trips[chat_id]:
                message = f"La posizione di ritrovo corrente è settata a: {day_trips[chat_id]['Location']}." \
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

    location = data[1]

    keyboard = [
        [InlineKeyboardButton("📍 Mostra sulla mappa", callback_data=ccd("SEND_LOCATION", location))],
        [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
    ]

    day_group = get_trip("Discesa", common.today(), chat_id)
    day_group["Location"] = location

    bot.edit_message_text(chat_id=chat_id,
                          message_id=update.callback_query.message.message_id,
                          text=f"Posizione impostata con successo: {location}",
                          reply_markup=InlineKeyboardMarkup(keyboard))

    for passenger_group in day_group["Temporary"], day_group["Permanent"]:
        for passenger in passenger_group:
            bot.send_message(chat_id=passenger,
                             text=f"Per il viaggio di ritorno,"
                             f" [{get_name(chat_id)}](tg://user?id={chat_id})"
                             f" ha impostato il luogo di ritrovo:\n📍 {location}.",
                             reply_markup=InlineKeyboardMarkup(keyboard))


def send_location(bot, update):
    chat_id = str(update.callback_query.message.chat_id)
    data = separate_callback_data(update.callback_query.data)

    location = data[1]

    latitude, longitude = common.locations[location]["Location"]

    bot.send_location(chat_id=chat_id, latitude=latitude, longitude=longitude)
