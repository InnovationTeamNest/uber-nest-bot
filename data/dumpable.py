# -*- coding: utf-8 -*-

import logging as log

from google.cloud import datastore

from data import dataset


def dump_data():
    """Dumps the whole dataset to Cloud Datastore"""
    if not empty_dataset():
        import json
        client = datastore.Client()
        key = client.key("Data", 1)
        client.delete(key)

        # Prepares the new entity
        data = datastore.Entity(key=key, exclude_from_indexes=("groups", "users", "drivers"))
        data["groups"] = json.dumps(dataset.groups)
        data["users"] = json.dumps(dataset.users)
        data["drivers"] = json.dumps(dataset.drivers)

        # Saves the entity
        client.put(data)
        return True
    else:
        log.critical("Trying to save empty data!")
        return False


def get_data():
    import json
    """Gets the data from Cloud Datastore"""
    if not empty_datastore():
        client = datastore.Client()
        data = client.get(client.key('Data', 1))

        dataset.groups = json.loads(data["groups"])
        dataset.users = json.loads(data["users"])
        dataset.drivers = json.loads(data["drivers"])
        return True
    else:
        return False


def print_data():
    """Prints to the Cloud Console Logs the current dataset. MUST BE used after get_data"""
    log.info("Drivers: " + str(dataset.drivers))
    log.info("Users: " + str(dataset.users))
    for direction in dataset.groups:
        for day in dataset.groups[direction]:
            log.info(f"Trips for {day} {direction}: {dataset.groups[direction][day]}")


def empty_datastore():
    """Verifies that the Cloud Datastore is empty"""
    return datastore.Client().get(datastore.Client().key("Data", 1)) is None


def empty_dataset():
    """Verifies if the input data from secrets.py is empty"""
    return dataset.groups == {} or dataset.users == {} or dataset.drivers == {}
