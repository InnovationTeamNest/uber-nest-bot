import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from data.data_api import get_trip, get_name, is_registered, get_all_trips_fixed_direction
from routing.filters import separate_callback_data, create_callback_data as ccd
from util import common


def show_bookings(bot, update):
    chat_id = str(update.callback_query.from_user.id)

    data = separate_callback_data(update.callback_query.data)

    message, keyboard = fetch_bookings(chat_id, data[1])

    bot.edit_message_text(chat_id=chat_id,
                          message_id=update.callback_query.message.message_id,
                          text=message,
                          reply_markup=keyboard,
                          parse_mode="Markdown")


def fetch_sessione():
    text = ["Riepilogo viaggi:"]
    today_number = datetime.datetime.today().weekday()

    for item in range(len(common.work_days)):
        _day = (item + today_number) % len(common.work_days)

        for direction in "Salita", "Discesa":
            bookings = get_all_trips_fixed_direction(direction, _day)

            if len(bookings) > 0:
                text.append(f"\n\n🗓 Viaggi di {common.days[_day].lower()} {datetime.datetime.today().day}")
                for time, driver in bookings:
                    trip = get_trip(direction, _day, driver)
                    # Raccolgo in una list comprehension le persone che partecipano al viaggio
                    people = [f"[{get_name(user)}](tg://user?id={user})" for user in trip["Temporary"]]

                    # Aggiungo ogni viaggio trovato alla lista
                    text.append(f"\n🚗 [{get_name(driver)}](tg://user?id={driver}) "
                                f"(*{time}*, {common.dir_name(direction)}): {', '.join(people)}\n")
            else:
                text.append(f"\n\n😱 Nessuno in viaggio per "
                            f"{common.days[_day].lower()} {datetime.datetime.today().day}.")

    keyboard = [
        [InlineKeyboardButton("🔂 Prenota",
                              callback_data=ccd("BOOKING", "DAY", "Temporary", "Lunedì"))],
        [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
    ]

    return "".join(text), InlineKeyboardMarkup(keyboard)


def fetch_bookings(chat_id, day):
    if common.is_weekday(day):
        text = [f"Lista dei viaggi di {day.lower()}:"]

        for direction in "Salita", "Discesa":
            text.append(f"\n\n{common.dir_name(direction)}\n")

            bookings = get_all_trips_fixed_direction(direction, day)

            if len(bookings) > 0:
                for time, driver in bookings:
                    trip = get_trip(direction, day, driver)
                    # Raccolgo in una list comprehension le persone che partecipano al viaggio
                    people = [f"[{get_name(user)}](tg://user?id={user})"
                              for mode in trip
                              if mode == "Temporary" or mode == "Permanent"
                              for user in trip[mode]]

                    # Aggiungo ogni viaggio trovato alla lista
                    text.append(f"\n🚗 [{get_name(driver)}](tg://user?id={driver})"
                                f" - 🕓 *{time}*:"
                                f"\n👥 {', '.join(people)}\n")
            else:
                text.append("\n🚶🏻‍♂ Nessuna persona in viaggio oggi.")

        if is_registered(chat_id):
            day_subkeyboard = []

            for wkday in common.work_days:
                ccd_text = "☑" if wkday == day else wkday[:2]
                day_subkeyboard.append(InlineKeyboardButton(ccd_text, callback_data=ccd("SHOW_BOOKINGS", wkday)))

            if common.is_booking_time():
                keyboard = [
                    day_subkeyboard,
                    [InlineKeyboardButton("🔂 Prenota una tantum",
                                          callback_data=ccd("BOOKING", "DAY", "Temporary", day))],
                    [InlineKeyboardButton("🔁 Prenota permanentemente",
                                          callback_data=ccd("BOOKING", "DAY", "Permanent", day))],
                    [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
                ]
            else:
                keyboard = [
                    day_subkeyboard,
                    [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
                ]
        else:
            keyboard = []

        return "".join(text), InlineKeyboardMarkup(keyboard)

    else:
        keyboard = [
            [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
        ]

        return f"{day} UberNEST non è attivo.", InlineKeyboardMarkup(keyboard)
