from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import secret_data
from util import common
from util.filters import separate_callback_data, create_callback_data


def show_bookings(bot, update):
    chat_id = update.callback_query.from_user.id

    data = separate_callback_data(update.callback_query.data)
    fetch_bookings(bot, chat_id, data[1])


def fetch_bookings(bot, chat_id, day):
    if common.is_weekday(day):
        text = "Lista dei viaggi di " + day.lower() + ":"

        for direction in "Salita", "Discesa":
            bookings = sorted([
                # Restituisce una tupla del tipo (ora, guidatore, chat_id) riordinata
                (secret_data.groups[direction][day][driver]["Time"], secret_data.users[driver]["Name"], driver)
                for driver in secret_data.groups[direction][day]
                if not secret_data.groups[direction][day][driver]["Suspended"]
            ])

            if len(bookings) > 0:
                text = text + "\n\n➡" + common.direction_to_name(direction) + "\n"
                for time, name, driver in bookings:
                    trip = secret_data.groups[direction][day][driver]
                    # Raccolgo in una list comprehension le persone che partecipano al viaggio
                    people = [secret_data.users[user]["Name"]
                              for mode in trip
                              if mode == "Temporary" or mode == "Permanent"
                              for user in trip[mode]]

                    # Aggiungo ogni viaggio trovato alla lista
                    text = text + "\n" + "🚗 " + name \
                           + " - 🕒 " + time + ":" \
                           + "\n👥 " + ", ".join(people) + "\n"
            else:
                text = text + "\n\n🚶🏻‍♂ 🚶🏻‍♂ Nessuna persona in viaggio " \
                       + common.direction_to_name(direction) + " oggi."

        if str(chat_id) in secret_data.users and common.booking_time():
            # Permetto l'uso della tastiera solo ai registrati
            keyboard = [
                [InlineKeyboardButton("Prenota una tantum",
                                      callback_data=create_callback_data("BOOKING", "DAY", "Temporary", day))],
                [InlineKeyboardButton("Prenota permanentemente",
                                      callback_data=create_callback_data("BOOKING", "DAY", "Permanent", day))],
                [InlineKeyboardButton("Esci", callback_data=create_callback_data("EXIT"))]
            ]
            bot.send_message(chat_id=chat_id, text=text,
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            bot.send_message(chat_id=chat_id, text=text)

    else:
        bot.send_message(chat_id=chat_id, text=day + " UberNEST non è attivo.")
