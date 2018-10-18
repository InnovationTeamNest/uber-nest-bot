# -*- coding: utf-8 -*-

import datetime

import pytz

import secrets

PAGE_SIZE = 5  # Numero di bottoni per pagina (in caso di visualizzazione di utenti multipli)
MAX_ATTEMPTS = 5  # Tentativi massimi di processo del webhook

# Localizzazione italiana dei nomi dei giorni della settimana
days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

# Sottoinsieme di days contenente i giorni lavorativi - cambiare se si vuole includere il sabato
work_days = days[:5]

# Inizio e fine del tempo ammesso di prenotazione
booking_start = datetime.time(6, 0)
booking_end = datetime.time(23, 50)

# Costo di ogni viaggio
trip_price = 0.50

# Il bot va disattivato dall'ultima settimana di dicembre (22/12) al 6/1, e nell'estate
no_trip_days = [
    datetime.date(2018, 11, 1),
    datetime.date(2018, 11, 2)
]  # Festa dei Santi e Morti

# Posizioni di parcheggio possibili
locations = [
    "Vietnam",
    "Povo 2 (fronte entrata)",
    "Povo 1 (parcheggio VIP)"
    "Povo 1 (cima scale)",
    "Povo 1 (fronte entrata)",
    "Povo 0",
    "Mesiano (fuori)",
    "Mesiano (fronte entrata)"
]


# Questi metodi gestiscono i giorni in formato stringa
def today():
    return day_to_string((datetime.datetime.now() + datetime.timedelta(hours=1 + is_dst())).weekday())


def tomorrow():
    return day_to_string((datetime.datetime.now() + datetime.timedelta(hours=1 + is_dst())).weekday() + 1)


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


def booking_time():
    """Controlla che l'orario attuale sia compreso all'interno degli orari di prenotazioni definiti sopra"""
    return booking_start <= now_time() <= booking_end


def dir_name(direction):
    if direction == "Salita":
        return "per Povo"
    elif direction == "Discesa":
        return "per il NEST"
    else:
        return " - "


def mode_name(mode):
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
    return [(direction, day, driver, mode, secrets.groups[direction][day][driver]["Time"])
            for direction in ("Salita", "Discesa")
            for day in work_days
            for driver in secrets.groups[direction][day]
            for mode in secrets.groups[direction][day][driver]
            if (mode == "Permanent" or mode == "Temporary" or mode == "SuspendedUsers")
            and person in secrets.groups[direction][day][driver][mode]]


def delete_driver(chat_id):
    """Metodo per cancellare tutti i dati di un autista"""
    del secrets.drivers[str(chat_id)]

    for direction in secrets.groups:
        for day in secrets.groups[direction]:
            if str(chat_id) in secrets.groups[direction][day]:
                del secrets.groups[direction][day][str(chat_id)]


def get_credits(input_creditor):
    """Restituisce un array di tuple contenente, dato un creditore, gli ID dei debitori e il valore."""
    return [(user, secrets.users[user]["Debit"][creditor]) for user in secrets.users
            for creditor in secrets.users[user]["Debit"] if creditor == input_creditor]


def get_debits(input_debitor):
    """Restituisce un array di tuple contenente, dato un debitore, gli ID dei creditore e il valore."""
    return [(creditor, secrets.users[input_debitor]["Debit"][creditor])
            for creditor in secrets.users[input_debitor]["Debit"]]


# I seguenti metodi sono stati piazzati qua perché c'entravano molto poco con qualsiasi altro file.
# Siate liberi di spostarli dove vi pare.

def alert_suspension(bot, direction, day, driver):
    trip = secrets.groups[direction][day][driver]
    driver_name = secrets.users[driver]["Name"]

    permanent_users = trip["Permanent"]
    temporary_users = trip["Temporary"]

    if trip["Suspended"]:
        for user in permanent_users:
            bot.send_message(chat_id=user,
                             text=f"Attenzione! {driver_name} ha sospeso il viaggio di {day}"
                                  f" {dir_name(direction)}. Non verrai addebitato per questa volta.")
        for user in temporary_users:
            bot.send_message(chat_id=user,
                             text=f"Attenzione! {driver_name} ha sospeso il viaggio di {day}"
                                  f" {dir_name(direction)}."
                                  f" La tua prenotazione scalerà alla settimana successiva.")
    else:
        for user in (permanent_users + temporary_users):
            bot.send_message(chat_id=user,
                             text=f"Attenzione! {driver_name} ha annullato la sospensione del viaggio di {day}"
                                  f" {dir_name(direction)}.")
