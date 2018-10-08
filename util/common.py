# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

import pytz

import secret_data

PAGE_SIZE = 5  # Numero di bottoni per pagina (in caso di visualizzazione di utenti multipli)
MAX_ATTEMPTS = 5  # Tentativi massimi di processo del webhook

# Localizzazione italiana dei nomi dei giorni della settimana
days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

# Sottoinsieme di days contenente i giorni lavorativi - cambiare se si vuole includere il sabato
work_days = days[:5]

# @Deprecated
# Localizzazione italiana delle direzioni specifiche e generiche
# direction_name = ["per Povo", "per il NEST"]
# direction_generic = ["Salita", "Discesa"]

# # Localizzazione dei metodi di prenotazioni come nel dataset e in italiano
# booking_types = ["Temporary", "Permanent"]
# booking_types_localized = ["Temporanea", "Permanente"]
# Stringa vuota usata in caso di risultati non presenti
# empty_str = " - "

# Inizio e fine del tempo ammesso di prenotazione
booking_start = datetime.time(6, 0)
booking_end = datetime.time(23, 30)

# Costo di ogni viaggio
trip_price = 0.50

# Il bot va disattivato dall'ultima settimana di dicembre (22/12) al 6/1, e nell'estate
no_trip_days = [datetime.date(2018, 11, 1), datetime.date(2018, 11, 2)]  # Festa dei Santi e Morti

# Posizioni di parcheggio possibili
locations = ["Povo 2", "Povo 1 (cima scale)", "Povo 1 (fronte entrata)",
             "Povo 0", "Vietnam", "Mesiano (fuori)", "Mesiano (fronte entrata)"]


# Questi metodi gestiscono i giorni in formato stringa
def today():
    return day_to_string(datetime.datetime.today().weekday())


def tomorrow():
    return day_to_string(datetime.datetime.today().weekday() + 1)


def day_to_string(number):
    return days[number % 7]


def string_to_day(string):
    try:
        return days.index(string)
    except ValueError:
        return " - "


def is_weekday(string):
    return 0 <= string_to_day(string) <= 4


# Questi metodi gestiscono le ore tenendo conto del DST
def now_time():
    """Ritorna l'orario corrente con DST"""
    return (datetime.datetime.now() + datetime.timedelta(hours=1 + is_dst())).time()


def is_dst():
    """Metodo che controlla che ci sia il DST utilizzando Pytz"""
    return pytz.timezone("Europe/Rome").localize(datetime.datetime.now()).dst() == datetime.timedelta(0, 3600)


# @Deprecated
# def get_trip_time(driver, day, direction):
#     "Restituisce una stringa del tipo "HH:MM"
#     try:
#         output = str(secret_data.groups[direction][day][driver]["Time"])
#     except KeyError:
#         log.debug("Nessuna partenza trovata per questa query: "
#                   + direction + ", " + day + ", " + driver)
#         output = None
#     return output


def booking_time():
    """Controlla che l'orario attuale sia compreso all'interno degli orari di prenotazioni definiti sopra"""
    return booking_start <= now_time() <= booking_end


def direction_to_name(direction):
    if direction == "Salita":
        return "per Povo"
    elif direction == "Discesa":
        return "per il NEST"
    else:
        return " - "


def localize_mode(mode):
    if mode == "Temporary":
        return "Temporanea"
    elif mode == "Permanent":
        return "Permanente"
    elif mode == "SuspendedUsers":
        return "Permanente (SOSPESA)"
    else:
        return " - "


def search_by_booking(person):
    """Ritorna tutte le prenotazioni di una certa persona"""
    return [(direction, day, driver, mode, secret_data.groups[direction][day][driver]["Time"])
            for direction in "Salita", "Discesa"
            for day in work_days
            for driver in secret_data.groups[direction][day]
            for mode in secret_data.groups[direction][day][driver]
            if (mode == "Permanent" or mode == "Temporary" or mode == "SuspendedUsers")
            and person in secret_data.groups[direction][day][driver][mode]]


def delete_driver(chat_id):
    """Metodo per cancellare tutti i dati di un autista"""
    del secret_data.drivers[str(chat_id)]

    for direction in secret_data.groups:
        for day in secret_data.groups[direction]:
            if str(chat_id) in secret_data.groups[direction][day]:
                del secret_data.groups[direction][day][str(chat_id)]


def get_credits(input_creditor):
    """Restituisce un array di tuple contenente, dato un creditore, gli ID dei debitori e il valore."""
    return [(user, secret_data.users[user]["Debit"][creditor]) for user in secret_data.users
            for creditor in secret_data.users[user]["Debit"] if creditor == input_creditor]


def get_debits(input_debitor):
    """Restituisce un array di tuple contenente, dato un debitore, gli ID dei creditore e il valore."""
    return [(creditor, secret_data.users[input_debitor]["Debit"][creditor])
            for creditor in secret_data.users[input_debitor]["Debit"]]


def alert_suspension(bot, direction, day, driver):
    trip = secret_data.groups[direction][day][driver]

    permanent_users = trip["Permanent"]
    temporary_users = trip["Temporary"]

    if trip["Suspended"]:
        for user in permanent_users:
            bot.send_message(chat_id=user,
                             text="Attenzione! " + secret_data.users[driver]
                                  + " ha sospeso il viaggio di " + day
                                  + " " + direction_to_name(direction)
                                  + ". Non verrai addebitato per questa volta.")
        for user in temporary_users:
            bot.send_message(chat_id=user,
                             text="Attenzione! " + secret_data.users[driver]
                                  + " ha sospeso il viaggio di " + day
                                  + " " + direction_to_name(direction)
                                  + ". La tua prenotazione scalerà alla settimana successiva.")
    else:
        for user in (permanent_users + temporary_users):
            bot.send_message(chat_id=user,
                             text="Attenzione! " + secret_data.users[driver]
                                  + " ha annullato la sospensione del viaggio di " + day
                                  + " " + direction_to_name(direction) + ".")