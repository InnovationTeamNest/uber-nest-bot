# -*- coding: utf-8 -*-

import datetime

import pytz

PAGE_SIZE = 5  # Numero di bottoni per pagina (in caso di visualizzazione di utenti multipli)
MAX_ATTEMPTS = 5  # Tentativi massimi di processo del webhook

# Localizzazione italiana dei nomi dei giorni della settimana
days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

# Sottoinsieme di days contenente i giorni lavorativi - cambiare se si vuole includere il sabato
work_days = days[:5]

# Emoji usate per gli slots dell'autista
emoji_numbers = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]

# Il bot va disattivato dall'ultima settimana di dicembre (22/12) al 6/1, e nell'estate
no_trip_days = [
    datetime.date(2018, 11, 1),
    datetime.date(2018, 11, 2)
]  # Festa dei Santi e Morti

# Url immagini
povo_url = "https://www.science.unitn.it/cisca/avvisi/titolo2.jpg"
nest_url = "http://giornaletrentino.it/image/policy:1.937279:1502009929/image/image.jpg"

# Posizioni di parcheggio possibili
locations = {
    "Vietnam": {
        "Location": (46.068628, 11.150435)
    },
    "Povo 2 (fronte entrata)": {
        "Location": (46.067849, 11.150428)
    },
    "Povo 1 (parcheggio VIP)": {
        "Location": (46.066634, 11.149003)
    },
    "Povo 1 (cima scale)": {
        "Location": (46.066888, 11.150411)
    },
    "Povo 1 (fronte entrata)": {
        "Location": (46.066861, 11.149995)
    },
    "Povo 0": {
        "Location": (46.065242, 11.150481)
    },
    "Mesiano (fuori)": {
        "Location": (46.067176, 11.139021)
    },
    "Mesiano (fronte entrata)": {
        "Location": (46.065315, 11.138967)
    },
}


# Questi metodi gestiscono i giorni in formato stringa
def today():
    return day_to_string((datetime.datetime.now() + datetime.timedelta(hours=1 + is_dst())).weekday())


def tomorrow():
    return day_to_string((datetime.datetime.now() + datetime.timedelta(hours=1 + is_dst())).weekday() + 1)


def is_sessione():
    return datetime.date(2019, 2, 15) >= datetime.datetime.today().date() >= datetime.date(2018, 12, 22)


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


def is_booking_time():
    """Controlla che l'orario attuale sia compreso all'interno degli orari di prenotazioni definiti sopra"""
    return datetime.time(2, 16) <= now_time() <= datetime.time(23, 59) or \
           datetime.time(0, 0) <= now_time() <= datetime.time(1, 59)


def dir_name(direction):
    if direction == "Salita":
        return "🎒 per Povo"
    elif direction == "Discesa":
        return "🏡 per il NEST"
    else:
        return " - "


def mode_name(mode):
    if mode == "Temporary":
        return "🔂 Temporanea"
    elif mode == "Permanent":
        return "🔁 Permanente"
    elif mode == "SuspendedUsers":
        return "🚫 Sospesa (Permanente)"
    else:
        return " - "
