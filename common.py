# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import logging as log

import pytz

import secret_data

# Questi dati vengono utilizzati da tutto il programma
days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
work_days = days[:5]

direction_name = ["per Povo", "per il NEST"]
direction_generic = ["Salita", "Discesa"]

booking_types = ["Temporary", "Permanent"]
booking_types_localized = ["Temporanea", "Permanente"]

empty_str = " - "

booking_start = datetime.time(6, 0)
booking_end = datetime.time(23,59)

trip_price = 0.50

# Il bot va disattivato dall'ultima settimana di dicembre (22/12) al 6/1, e nell'estate
no_trip_days = [datetime.date(2018, 11, 1), datetime.date(2018, 11, 2)]  # Festa dei Santi e Morti


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
        return empty_str


def is_weekday(string):
    return 0 <= string_to_day(string) <= 4


# Questi metodi gestiscono le ore tenendo conto del DST
def now_time():
    """Ritorna l'orario corrente con DST"""
    return (datetime.datetime.now() + datetime.timedelta(hours=1 + is_dst())).time()


def is_dst():
    """Metodo che controlla che ci sia il DST utilizzando Pytz"""
    return pytz.timezone("Europe/Rome").localize(datetime.datetime.now()).dst() == datetime.timedelta(0, 3600)


def get_trip_time(driver, date, direction):
    """Restituisce una stringa del tipo "HH:MM" """
    try:
        output = str(secret_data.groups[direction][date][driver]["Time"])
    except KeyError:
        log.debug("Nessuna partenza trovata per questa query: "
                  + direction + ", " + date + ", " + driver)
        output = None
    return output


def booking_time():
    """Controlla che l'orario attuale sia compreso all'interno degli orari di prenotazioni definiti sopra"""
    return booking_start <= now_time() <= booking_end


def direction_to_name(direction):
    try:
        return direction_name[direction_generic.index(direction)]
    except ValueError:
        return empty_str


def localize_mode(mode):
    try:
        return booking_types_localized[booking_types.index(mode)]
    except ValueError:
        return empty_str


def search_by_booking(person):
    return [[direction, day, driver, mode]
            for direction in secret_data.groups
            for day in secret_data.groups[direction]
            for driver in secret_data.groups[direction][day]
            for mode in secret_data.groups[direction][day][driver]
            if person in secret_data.groups[direction][day][driver][mode]]


def delete_driver(chat_id):
    del secret_data.drivers[str(chat_id)]

    for direction in secret_data.groups:
        for day in secret_data.groups[direction]:
            if str(chat_id) in secret_data.groups[direction][day]:
                del secret_data.groups[direction][day][str(chat_id)]
