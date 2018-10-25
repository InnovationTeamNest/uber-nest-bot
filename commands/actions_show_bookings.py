from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import secrets
from util import common
from util.filters import separate_callback_data, create_callback_data as ccd


def show_bookings(bot, update):
    chat_id = str(update.callback_query.from_user.id)

    data = separate_callback_data(update.callback_query.data)

    message, keyboard = fetch_bookings(chat_id, data[1])

    bot.edit_message_text(chat_id=chat_id,
                          message_id=update.callback_query.message.message_id,
                          text=message,
                          reply_markup=keyboard,
                          parse_mode="Markdown")


def fetch_bookings(chat_id, day):
    if common.is_weekday(day):
        text = [f"Lista dei viaggi di {day.lower()}:"]

        for direction in "Salita", "Discesa":
            text.append(f"\n\n{common.dir_name(direction)}\n")

            bookings = sorted([
                (
                    secrets.groups[direction][day][driver]["Time"],  # Orario di partenza
                    driver  # Chat ID dell'autista
                )
                for driver in secrets.groups[direction][day]
                if not secrets.groups[direction][day][driver]["Suspended"]
            ])

            if len(bookings) > 0:
                for time, driver in bookings:
                    trip = secrets.groups[direction][day][driver]
                    # Raccolgo in una list comprehension le persone che partecipano al viaggio
                    people = [f"[{secrets.users[user]['Name']}](tg://user?id={user})"
                              for mode in trip
                              if mode == "Temporary" or mode == "Permanent"
                              for user in trip[mode]]

                    # Aggiungo ogni viaggio trovato alla lista
                    text.append(f"\n🚗 [{secrets.users[driver]['Name']}](tg://user?id={driver})"
                                f" - 🕓 *{time}*:"
                                f"\n👥 {', '.join(people)}\n")
            else:
                text.append("\n🚶🏻‍♂ Nessuna persona in viaggio oggi.")

        if chat_id in secrets.users and common.booking_time():
            # Permetto l'uso della tastiera solo ai registrati
            keyboard = [
                [InlineKeyboardButton("🔂 Prenota una tantum",
                                      callback_data=ccd("BOOKING", "DAY", "Temporary", day))],
                [InlineKeyboardButton("🔁 Prenota permanentemente",
                                      callback_data=ccd("BOOKING", "DAY", "Permanent", day))],
                [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
            ]
        else:
            keyboard = [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]

        return "".join(text), InlineKeyboardMarkup(keyboard)

    else:
        return f"{day} UberNEST non è attivo.", \
               InlineKeyboardMarkup([[
                   InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]])
