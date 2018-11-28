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


def delete_user(chat_id):
    """
    Wipes a user from the system, including driver data if present
    :param chat_id: The chat_id to delete.
    :return:
    """
    del users[chat_id]
    if is_driver(chat_id):
        delete_driver(chat_id)


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
    """
    Sets a debit to an arbitrary velue
    :param chat_id: The debitor
    :param creditor: The creditor
    :param value: The value to be placed
    :return:
    """
    users[chat_id]["Debit"][creditor] = value


def get_all_debits(chat_id):
    """
    Returns all the debits, given a single user
    :param chat_id: The chat_id to get the debits from.
    :return: A dictionary with keys containing chat_ids and values containing debits
    """
    return users[chat_id]["Debit"]


def remove_single_debit(chat_id, creditor):
    """
    Wipes a debit from a user's debit list.
    :param chat_id: The chat_id of the debitor.
    :param creditor: The creditor to delete from the list.
    :return:
    """
    del users[chat_id]["Debit"][creditor]

# Autisti


def add_driver(chat_id, slots):
    """
    Adds a currently registered user to the driver list.
    :param chat_id: The chat_id to add.
    :param slots:T The amount of seats, driver excluded
    :return:
    """
    drivers[chat_id] = {"Slots": slots}


def is_driver(chat_id):
    """
    Checks whether a registered user is also a driver.
    :param chat_id: The chat_id to check.
    :return: True if the user is registered.
    """
    return chat_id in drivers


def delete_driver(chat_id):
    """
    Wipes a driver from the driver list.
    :param chat_id: The chat_id to remove.
    :return:
    """
    del drivers[chat_id]

    for direction in groups:
        for day in groups[direction]:
            if chat_id in groups[direction][day]:
                del groups[direction][day][chat_id]

    for user in users:
        if chat_id in users[user]["Debit"]:
            del users[user]["Debit"][chat_id]


def get_slots(chat_id):
    """
    Returns the number of slots, given a driver.
    :param chat_id: The chat_id of the driver.
    :return: An integer, representing the number of available slots.
    """
    return drivers[chat_id]["Slots"]


# Trip multipli


def get_trip_group(direction, day):
    """
    Returns all the trips for a given tuple (direction, day).
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì")
    :return: A dictionary containing entries for each trip.
    """
    return groups[direction][day]


def all_directions():
    """
    :return: Returns all the available directions.
    """
    return groups.keys()


# Trip singolo


def new_trip(direction, day, driver, time):
    """
    Adds a new trip to the system.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :param time: The time of departure.
    :return:
    """
    groups[direction][day][driver] = {"Time": time,
                                      "Permanent": [],
                                      "Temporary": [],
                                      "SuspendedUsers": [],
                                      "Suspended": False}


def get_trip(direction, day, driver):
    """
    Returns a dictionary entry for a given trip.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :return: A dictionary entry for the requested trip.
    """
    return groups[direction][day][driver]


def get_time(direction, day, driver):
    """
    Returns the time of departure of a given trip.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :return: A string representing the departure time, formatted as %H:%M (24h)
    """
    return groups[direction][day][driver]["Time"]


def is_suspended(direction, day, driver):
    """
    REturns whether a given trip is suspended.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :return: True if the trip is suspended.
    """
    return groups[direction][day][driver]["Suspended"]


def suspend_trip(direction, day, driver):
    """
    Suspends a given trip.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :return:
    """
    groups[direction][day][driver]["Suspended"] = True


def unsuspend_trip(direction, day, driver):
    """
    Removes a trip from its suspension.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :return:
    """
    groups[direction][day][driver]["Suspended"] = False


def add_passenger(direction, day, driver, mode, chat_id):
    """
    Adds a passenger to a given trip.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :param mode: The mode to register the booking as.
    :param chat_id: The chat_id of the passenger.
    :return:
    """
    groups[direction][day][driver][mode].append(chat_id)


def remove_passenger(direction, day, driver, mode, chat_id):
    """
    Removes a passenger from a given trip.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :param mode: The mode the booking was registered as.
    :param chat_id: The chat_id of the passenger.
    :raises: KeyError
    :return:
    """
    groups[direction][day][driver][mode].remove(chat_id)


def remove_trip(direction, day, driver):
    """
    Removes a trip from the system.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :return:
    """
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
