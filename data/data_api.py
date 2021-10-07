# -*- coding: utf-8 -*-
import logging

from sqlalchemy import text

import data.dataset as dt
from util.common import work_days
from .database import engine


# Users

def add_user(chat_id: int, user: str) -> bool:
    """
    This function adds a user to a dataset, given its chat id.
    :param chat_id: The chat_id of the user.
    :param user: The username.
    :return: True if the operation succeded.
    """
    try:
        with engine().connect() as conn:
            conn.execute(text("INSERT INTO Person (person_id, full_name) VALUES (:pid, :fn)"),
                         {"pid": chat_id, "fn": user})
            conn.commit()
            return True
    except Exception as ex:
        logging.error(f"Failed to insert Person: {ex}.", exc_info=True)
        raise Exception(ex)


def is_registered(chat_id):
    """
    Checks whether a chat_id is already in the database.
    :param chat_id: The chat_id to check.
    :return: True if the user is registered, else False.
    """
    try:
        with engine().connect() as conn:
            result = conn.execute(text("SELECT person_id from Person where person_id = :pid"),
                                  {"pid": chat_id})
            return len(result) == 1  # Cannot be more, since person_id is primary key on the database
    except Exception as ex:
        logging.error(f"Failed to retrieve Person: {ex}.", exc_info=True)
        raise Exception(ex)


def get_name(chat_id):
    """
    Returns a chat_id's relative username
    :param chat_id: The chat_id to check.
    :return: A string representing the relative username
    """
    try:
        with engine().connect() as conn:
            result = conn.execute(text("SELECT person_id from Person where person_id = :pid"),
                                  {"pid": chat_id})
            if len(result) == 0:
                raise ValueError("User is not registered, cannot retrieve name.")
            elif len(result) < 0 or len(result) > 1:
                raise ValueError(f"Error in DB data: {result}")

            return result[0].person_id
    except Exception as ex:
        logging.error(f"Failed to retrieve Person's name: {ex}.", exc_info=True)
        raise Exception(ex)


def all_users():
    """
    :return: Returns all the chat_id present in the system.
    """
    try:
        with engine().connect() as conn:
            result = conn.execute(text("SELECT person_id from Person"))
            return [item.person_id for item in result]
    except Exception as ex:
        logging.error(f"Failed to retrieve all People: {ex}.", exc_info=True)
        raise Exception(ex)


def delete_user(chat_id):
    """
    Wipes a user from the system, including driver data if present
    :param chat_id: The chat_id to delete.
    :return: True if the operation succeeded.
    """
    try:
        with engine().connect() as conn:
            conn.execute(text("DELETE FROM Driver WHERE driver_id = :did"),
                         {"did": chat_id})
            conn.execute(text("DELETE FROM Person WHERE person_id = :pid"),
                         {"pid": chat_id})
            conn.commit()
            return True
    except Exception as ex:
        logging.error(f"Failed to remove Person: {ex}.", exc_info=True)
        raise Excepion(ex)


# Debiti


def get_single_debit(chat_id, creditor):
    """
    Gets the amount of money a person owes to a creditor.
    :param chat_id: The debitor
    :param creditor: The creditor
    :return: The value owed
    """
    try:
        return dt.users[chat_id]["Debit"][creditor]
    except KeyError:
        return None


def set_single_debit(chat_id, creditor, value):
    """
    Sets a debit to an arbitrary velue
    :param chat_id: The debitor
    :param creditor: The creditor
    :param value: The value to be placed
    :return:
    """
    dt.users[chat_id]["Debit"][creditor] = value


def quick_debit_edit(chat_id, creditor, mode):
    """
    Quick edit mode for any debit. Gets the added/subtracted value from common.py. Available options:
    +, addition
    -, subtraction
    0, removal
    :param chat_id: The debitor
    :param creditor: The creditor
    :param mode: The mode to operate with
    :return:
    """

    if mode == "+":
        try:
            dt.users[chat_id]["Debit"][creditor] += 1
        except KeyError:
            dt.users[chat_id]["Debit"][creditor] = 1

    elif mode == "-":
        try:
            dt.users[chat_id]["Debit"][creditor] -= 1
        except KeyError:
            dt.users[chat_id]["Debit"][creditor] = -1

    elif mode == "0":
        dt.users[chat_id]["Debit"][creditor] = 0

    else:
        raise ValueError

    return dt.users[chat_id]["Debit"][creditor]


def get_all_debits(chat_id):
    """
    Returns all the debits, given a single user
    :param chat_id: The chat_id to get the debits from.
    :return: A dictionary with keys containing chat_ids and values containing debits
    """
    return dt.users[chat_id]["Debit"]


def remove_single_debit(chat_id, creditor):
    """
    Wipes a debit from a user's debit list.
    :param chat_id: The chat_id of the debitor.
    :param creditor: The creditor to delete from the list.
    :return:
    """
    del dt.users[chat_id]["Debit"][creditor]


# Autisti


def add_driver(chat_id, slots):
    """
    Adds a currently registered user to the driver list.
    :param chat_id: The chat_id to add.
    :param slots:T The amount of seats, driver excluded
    :return:
    """
    dt.drivers[chat_id] = {"Slots": slots}


def is_driver(chat_id):
    """
    Checks whether a registered user is also a driver.
    :param chat_id: The chat_id to check.
    :return: True if the user is registered.
    """
    return chat_id in dt.drivers


def delete_driver(chat_id):
    """
    Wipes a driver from the driver list.
    :param chat_id: The chat_id to remove.
    :return:
    """
    del dt.drivers[chat_id]

    for direction in dt.groups:
        for day in dt.groups[direction]:
            if chat_id in dt.groups[direction][day]:
                del dt.groups[direction][day][chat_id]

    for user in dt.users:
        if chat_id in dt.users[user]["Debit"]:
            del dt.users[user]["Debit"][chat_id]


def get_slots(chat_id):
    """
    Returns the number of slots, given a driver.
    :param chat_id: The chat_id of the driver.
    :return: An integer, representing the number of available slots.
    """
    return dt.drivers[chat_id]["Slots"]


# Trip multipli


def get_trip_group(direction, day):
    """
    Returns all the trips for a given tuple (direction, day).
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì")
    :return: A dictionary containing entries for each trip.
    """
    return dt.groups[direction][day]


def all_directions():
    """
    :return: Returns all the available directions.
    """
    return dt.groups.keys()


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
    dt.groups[direction][day][driver] = {"Time": time,
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
    try:
        return dt.groups[direction][day][driver]
    except KeyError:
        return None


def get_time(direction, day, driver):
    """
    Returns the time of departure of a given trip.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :return: A string representing the departure time, formatted as %H:%M (24h)
    """
    try:
        return dt.groups[direction][day][driver]["Time"]
    except KeyError:
        return None


def is_suspended(direction, day, driver):
    """
    REturns whether a given trip is suspended.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :return: True if the trip is suspended.
    """
    try:
        return dt.groups[direction][day][driver]["Suspended"]
    except KeyError:
        return None


def suspend_trip(direction, day, driver):
    """
    Suspends a given trip.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :return:
    """
    dt.groups[direction][day][driver]["Suspended"] = True


def unsuspend_trip(direction, day, driver):
    """
    Removes a trip from its suspension.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :return:
    """
    dt.groups[direction][day][driver]["Suspended"] = False


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
    dt.groups[direction][day][driver][mode].append(chat_id)


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
    dt.groups[direction][day][driver][mode].remove(chat_id)


def remove_trip(direction, day, driver):
    """
    Removes a trip from the system.
    :param direction: "Salita" or "Discesa".
    :param day: A day spanning the whole work week ("Lunedì"-"Venerdì").
    :param driver: The chat_id of the driver.
    :return:
    """
    del dt.groups[direction][day][driver]


# Comandi avanzati


def get_bookings(person):
    """Ritorna tutte le prenotazioni di una certa persona"""
    return [(direction, day, driver, mode, dt.groups[direction][day][driver]["Time"])
            for direction in ("Salita", "Discesa")
            for day in work_days
            for driver in dt.groups[direction][day]
            for mode in dt.groups[direction][day][driver]
            if (mode == "Permanent" or mode == "Temporary" or mode == "SuspendedUsers")
            and person in dt.groups[direction][day][driver][mode]]


def get_bookings_day_nosusp(person, day):
    return [(direction, driver, mode, dt.groups[direction][day][driver]["Time"])
            for direction in ("Salita", "Discesa")
            for driver in dt.groups[direction][day]
            if not dt.groups[direction][day][driver]["Suspended"]
            for mode in dt.groups[direction][day][driver]
            if (mode == "Permanent" or mode == "Temporary")
            and person in dt.groups[direction][day][driver][mode]]


def get_credits(input_creditor):
    """Restituisce un array di tuple contenente, dato un creditore, gli ID dei debitori e il valore."""
    return [(user, dt.users[user]["Debit"][creditor]) for user in dt.users
            for creditor in dt.users[user]["Debit"] if creditor == input_creditor]


def get_debit_tuple(input_debitor):
    """Restituisce un array di tuple contenente, dato un debitore, gli ID dei creditore e il valore."""
    return [(creditor, dt.users[input_debitor]["Debit"][creditor])
            for creditor in dt.users[input_debitor]["Debit"]]


def get_new_debitors(chat_id):
    # Resituisce una lista di tuple del tipo (Nome, ID)
    return sorted([
        (
            dt.users[user]["Name"],
            user
        )
        for user in dt.users
        if user != chat_id and chat_id not in dt.users[user]["Debit"]
    ])


def get_new_passengers(chat_id):
    # Resituisce una lista di tuple del tipo (Nome, ID)
    return sorted([
        (
            dt.users[user]["Name"],
            user
        )
        for user in dt.users
        if user != chat_id
    ])


def get_all_trips_fixed_direction(direction, day):
    return sorted([
        (
            dt.groups[direction][day][driver]["Time"],  # Orario di partenza
            driver  # Chat ID dell'autista
        )
        for driver in dt.groups[direction][day]
        if not dt.groups[direction][day][driver]["Suspended"]
    ])


def get_all_trips_day(day):
    return sorted([
        # Restituisce una tupla del tipo (ora, guidatore, direzione, chat_id) riordinata
        (
            dt.groups[direction][day][driver]["Time"],
            dt.users[driver]["Name"], direction, driver
        )
        for direction in dt.groups
        for driver in dt.groups[direction][day]
    ])
