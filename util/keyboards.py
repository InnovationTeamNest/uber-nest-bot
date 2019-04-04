# -*- coding: utf-8 -*-
import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from data.data_api import is_driver, get_slots, get_trip, is_suspended, get_all_trips_day
from routing.filters import create_callback_data as ccd
from util import common


#
# Tastiera chiamata dal menù /me. Cambia a seconda che il guidatore è un autista o meno.
#
def me_keyboard(chat_id):
    keyboard = []
    if is_driver(chat_id):
        money_string = "💰 Gestire i miei debiti e crediti"
        driver_string = "🚫 Smettere di essere un autista"
        keyboard.append([InlineKeyboardButton("🚗 Gestire i miei viaggi", callback_data=ccd("ME", "TRIPS"))])
        keyboard.append([InlineKeyboardButton(f"{common.emoji_numbers[get_slots(chat_id)]}"
                                              f" Modificare il numero di posti", callback_data=ccd("ME", "ED_DR_SL"))])
    else:
        money_string = "💸 Gestire i miei debiti"
        driver_string = "🚗 Diventare un autista"

    keyboard.append([InlineKeyboardButton(money_string, callback_data=ccd("MONEY"))])
    keyboard.append([InlineKeyboardButton(driver_string, callback_data=ccd("ME", "DRIVER"))])
    keyboard.append([InlineKeyboardButton("❌ Cancellarmi da UberNEST", callback_data=ccd("ME", "US_RE"))])
    keyboard.append([InlineKeyboardButton("🔚 Uscire", callback_data=ccd("EXIT"))])

    return InlineKeyboardMarkup(keyboard)


#
# Tastiera chiamata dal menù TRIPS di /me. Mostra tutti i viaggi di un certo autista, inclusi i posti liberi
# oppure SOSP se il viaggio risulta sospeso.
#
def trips_keyboard(chat_id):
    keyboard = [[InlineKeyboardButton("Aggiungi un nuovo viaggio", callback_data=ccd("TRIPS", "ADD"))]]
    today_number = datetime.datetime.today().weekday()

    for item in range(len(common.days)):
        day = common.day_to_string((item + today_number) % len(common.days))

        if day == "Sabato" or day == "Domenica":  # Sabato, domenica
            continue

        for direction in "Salita", "Discesa":
            try:
                group = get_trip(direction, day, chat_id)

                if group["Suspended"]:
                    counter = "SOSP."
                else:
                    counter = f"{len(group['Permanent']) + len(group['Temporary'])}"

                if common.is_sessione():
                    shown_day = f"{day} {datetime.datetime.today().day + item}"
                else:
                    shown_day = day

                keyboard.append(
                    [InlineKeyboardButton(f"{shown_day}: {group['Time']}"
                                          f" {common.dir_name(direction)} ({counter})",
                                          callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))])
            except Exception:  # Viaggio non segnato...
                continue

    keyboard.append([InlineKeyboardButton("↩ Indietro", callback_data=ccd("ME_MENU"))])
    keyboard.append([InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))])

    return InlineKeyboardMarkup(keyboard)


#
# Tastiera chiamata con i menù di /prenota. mode e day sono due oggetti di tipo /prenota.
# Al suo interno non vengono mai visualizzati i viaggi sospesi.
# Vi sono inoltre due bottoni per cambiare liberamente tra la visualizzazione prenotzione e la
# visualizzazione giorno semplice.
#
def booking_keyboard(mode, day, show_bookings=True):
    keyboard = []

    if common.is_sessione():
        today_number = datetime.datetime.today().weekday()
        for item in range(len(common.days)):
            _day = common.day_to_string((item + today_number) % len(common.days))

            if _day == "Sabato" or _day == "Domenica":  # Sabato, domenica
                continue

            bookings = get_all_trips_day(_day)

            for time, name, direction, driver in bookings:
                if not is_suspended(direction, _day, driver):
                    shortened_direction = "Povo" if direction == "Salita" else "NEST"
                    keyboard.append(
                        [InlineKeyboardButton(f"🚗 {name.split(' ')[-1]}/"
                                              f"{_day[:2]} "
                                              f"{datetime.datetime.today().day + item} "
                                              f"{time}/{shortened_direction}",
                                              callback_data=ccd("BOOKING", "CONFIRM", direction,
                                                                _day, driver, "Temporary"))])

        keyboard.append([InlineKeyboardButton(f"Vai a /oggi", callback_data=ccd("SHOW_BOOKINGS", "Lunedì"))])
        keyboard.append([InlineKeyboardButton("↩ Indietro", callback_data=ccd("BOOKING_MENU"))])

    else:
        if show_bookings:
            bookings = get_all_trips_day(day)

            for time, name, direction, driver in bookings:
                if not is_suspended(direction, day, driver):
                    keyboard.append(
                        [InlineKeyboardButton(f"🚗 {name.split(' ')[-1]} 🕓 {time} "
                                              f"{common.dir_name(direction)}",
                                              callback_data=ccd("BOOKING", "CONFIRM", direction, day, driver, mode))])

        day_subkeyboard = []
        for wkday in common.work_days:
            text = "☑" if wkday == day and show_bookings else wkday[:2]
            day_subkeyboard.append(InlineKeyboardButton(text, callback_data=ccd("BOOKING", "DAY", mode, wkday)))

        alternate_text = "🔂 Cambia metodo (Temp.)" if mode == "Permanent" else "🔁 Cambia metodo (Perm.)"
        alternate_payload = "Temporary" if mode == "Permanent" else "Permanent"
        alternate_ccd = ccd("BOOKING", "DAY", alternate_payload, day) if show_bookings else \
            ccd("BOOKING", "START", alternate_payload)

        keyboard.append(day_subkeyboard)
        keyboard.append([InlineKeyboardButton(alternate_text, callback_data=alternate_ccd)])

        if show_bookings:
            keyboard.append(
                [InlineKeyboardButton(f"Vai a /{day[:-1].lower()}ì", callback_data=ccd("SHOW_BOOKINGS", day))])
        else:
            keyboard.append([InlineKeyboardButton("↩ Indietro", callback_data=ccd("BOOKING_MENU"))])

    keyboard.append([InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))])

    return InlineKeyboardMarkup(keyboard)


def booking_menu_keyboard():
    if common.is_sessione():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔂 Prenotare",
                                  callback_data=ccd("BOOKING", "START", "Temporary"))],
            [InlineKeyboardButton("📚 Gestire le mie prenotazioni",
                                  callback_data=ccd("EDIT_BOOK", "LIST"))],
            [InlineKeyboardButton("ℹ Informarmi sulle modalità",
                                  callback_data=ccd("INFO_BOOK"))],
            [InlineKeyboardButton("🔚 Uscire", callback_data=ccd("EXIT"))]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔂 Prenotare una-tantum",
                                  callback_data=ccd("BOOKING", "START", "Temporary"))],
            [InlineKeyboardButton("🔁 Prenotare in maniera permanente",
                                  callback_data=ccd("BOOKING", "START", "Permanent"))],
            [InlineKeyboardButton("📚 Gestire le mie prenotazioni",
                                  callback_data=ccd("EDIT_BOOK", "LIST"))],
            [InlineKeyboardButton("ℹ Informarmi sulle modalità",
                                  callback_data=ccd("INFO_BOOK"))],
            [InlineKeyboardButton("🔚 Uscire", callback_data=ccd("EXIT"))]
        ])
