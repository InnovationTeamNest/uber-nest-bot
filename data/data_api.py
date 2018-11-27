# -*- coding: utf-8 -*-

from data.dataset import drivers, users, groups
from util.common import work_days


# Utenti


def add_user(chat_id, user):
    """
    This function adds a user to a dataset, given its chat id.
    :param chat_id: The chat_id of the user.
    :param user: The username.
    :return:
    """
    users[str(chat_id)] = {"Name": str(user), "Debit": {}}


def is_registered(chat_id):
    """
    Checks whether a chat_id is already in the database.
    :param chat_id: The chat_id to check.
    :return: True if the user is registered, else False.
    """
    return str(chat_id) in users


def get_name(chat_id):
    """
    Returns a chat_id's relative username
    :param chat_id: The chat_id to check.
    :return: A string representing the relative username
    """
    return users[chat_id]


def all_users():
    """
    :return: Returns all the chat_id present in the system.
    """
    return users.keys()


# Debiti


def get_single_debit(chat_id, creditor):
    """
    Gets the amount of money a person owes to a creditor.
    :param chat_id: The debitor
    :param creditor: The creditor
    :return: The value owed
    """
    return users[chat_id]["Debit"][creditor]


def set_single_debit(chat_id, creditor, value):
    users[chat_id]["Debit"][creditor] = value


def get_all_debits(chat_id):
    return users[chat_id]["Debit"]


def remove_single_debit(chat_id, creditor):
    del users[chat_id]["Debit"][creditor]


def delete_user(chat_id):
    del users[chat_id]
    if is_driver(chat_id):
        delete_driver(chat_id)


# Autisti


def add_driver(chat_id, slots):
    drivers[chat_id] = {"Slots": slots}


def is_driver(chat_id):
    return chat_id in drivers


def delete_driver(chat_id):
    del drivers[chat_id]

    for direction in groups:
        for day in groups[direction]:
            if chat_id in groups[direction][day]:
                del groups[direction][day][chat_id]

    for user in users:
        if chat_id in users[user]["Debit"]:
            del users[user]["Debit"][chat_id]


def get_slots(chat_id):
    return drivers[chat_id]["Slots"]


# Trip multipli


def get_trip_group(direction, day):
    return groups[direction][day]


def all_directions():
    return groups.keys()


# Trip singolo


def new_trip(direction, day, driver, time):
    groups[direction][day][driver] = {"Time": time,
                                      "Permanent": [],
                                      "Temporary": [],
                                      "SuspendedUsers": [],
                                      "Suspended": False}


def get_trip(direction, day, driver):
    return groups[direction][day][driver]


def get_time(direction, day, driver):
    return groups[direction][day][driver]["Time"]


def is_suspended(direction, day, driver):
    return groups[direction][day][driver]["Suspended"]


def suspend_trip(direction, day, driver):
    groups[direction][day][driver]["Suspended"] = True


def unsuspend_trip(direction, day, driver):
    groups[direction][day][driver]["Suspended"] = False


def add_passenger(direction, day, driver, mode, chat_id):
    groups[direction][day][driver][mode].append(chat_id)


def remove_passenger(direction, day, driver, mode, chat_id):
    groups[direction][day][driver][mode].remove(chat_id)


def remove_trip(direction, day, driver):
    del groups[direction][day][driver]


# Comandi avanzati


def get_bookings(person):
    """Ritorna tutte le prenotazioni di una certa persona"""
    return [(direction, day, driver, mode, groups[direction][day][driver]["Time"])
            for direction in ("Salita", "Discesa")
            for day in work_days
            for driver in groups[direction][day]
            for mode in groups[direction][day][driver]
            if (mode == "Permanent" or mode == "Temporary" or mode == "SuspendedUsers")
            and person in groups[direction][day][driver][mode]]


def get_bookings_day_nosusp(person, day):
    return [(direction, driver, mode, groups[direction][day][driver]["Time"])
            for direction in ("Salita", "Discesa")
            for driver in groups[direction][day]
            for mode in groups[direction][day][driver]
            if (mode == "Permanent" or mode == "Temporary")
            and person in groups[direction][day][driver][mode]]


def get_credits(input_creditor):
    """Restituisce un array di tuple contenente, dato un creditore, gli ID dei debitori e il valore."""
    return [(user, users[user]["Debit"][creditor]) for user in users
            for creditor in users[user]["Debit"] if creditor == input_creditor]


def get_debit_tuple(input_debitor):
    """Restituisce un array di tuple contenente, dato un debitore, gli ID dei creditore e il valore."""
    return [(creditor, users[input_debitor]["Debit"][creditor])
            for creditor in users[input_debitor]["Debit"]]


def get_new_debitors(chat_id):
    # Resituisce una lista di tuple del tipo (Nome, ID)
    return sorted([
        (
            users[user]["Name"],
            user
        )
        for user in users
        if user != chat_id and chat_id not in users[user]["Debit"]
    ])


def get_new_passengers(chat_id):
    # Resituisce una lista di tuple del tipo (Nome, ID)
    return sorted([
        (
            users[user]["Name"],
            user
        )
        for user in users
        if user != chat_id
    ])


def get_all_trips_fixed_direction(direction, day):
    return sorted([
        (
            groups[direction][day][driver]["Time"],  # Orario di partenza
            driver  # Chat ID dell'autista
        )
        for driver in groups[direction][day]
        if not groups[direction][day][driver]["Suspended"]
    ])


def get_all_trips_day(day):
    return sorted([
        # Restituisce una tupla del tipo (ora, guidatore, direzione, chat_id) riordinata
        (
            groups[direction][day][driver]["Time"],
            users[driver]["Name"], direction, driver
        )
        for direction in groups
        for driver in groups[direction][day]
    ])
