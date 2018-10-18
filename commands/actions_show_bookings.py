from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import secrets
from util import common
from util.filters import separate_callback_data, create_callback_data as ccd


def show_bookings(bot, update):
    chat_id = update.callback_query.from_user.id

    data = separate_callback_data(update.callback_query.data)
    fetch_bookings(bot, chat_id, data[1])


def fetch_bookings(bot, chat_id, day):
    if common.is_weekday(day):
        text = [f"Lista dei viaggi di {day.lower()}:"]

        for direction in "Salita", "Discesa":
            bookings = sorted([
                # Restituisce una tupla del tipo (ora, guidatore, chat_id) riordinata
                (secrets.groups[direction][day][driver]["Time"], secrets.users[driver]["Name"], driver)
                for driver in secrets.groups[direction][day]
                if not secrets.groups[direction][day][driver]["Suspended"]
            ])

            if len(bookings) > 0:
                text.append("\n\n➡" + common.dir_name(direction) + "\n")
                for time, name, driver in bookings:
                    trip = secrets.groups[direction][day][driver]
                    # Raccolgo in una list comprehension le persone che partecipano al viaggio
                    people = [secrets.users[user]["Name"]
                              for mode in trip
                              if mode == "Temporary" or mode == "Permanent"
                              for user in trip[mode]]

                    # Aggiungo ogni viaggio trovato alla lista
                    text.append("\n" + "🚗 " + name \
                                + " - 🕒 " + time + ":" \
                                + "\n👥 " + ", ".join(people) + "\n")
            else:
                text.append("\n\n🚶🏻‍♂ 🚶🏻‍♂ Nessuna persona in viaggio " \
                            + common.dir_name(direction) + " oggi.")

        if str(chat_id) in secrets.users and common.booking_time():
            # Permetto l'uso della tastiera solo ai registrati
            keyboard = [
                [InlineKeyboardButton("Prenota una tantum", callback_data=ccd("BOOKING", "DAY", "Temporary", day))],
                [InlineKeyboardButton("Prenota permanentemente",
                                      callback_data=ccd("BOOKING", "DAY", "Permanent", day))],
                [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
            ]
            bot.send_message(chat_id=chat_id, text="".join(text),
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            bot.send_message(chat_id=chat_id, text=text)

    else:
        bot.send_message(chat_id=chat_id, text=day + " UberNEST non è attivo.")
