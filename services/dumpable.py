# -*- coding: utf-8 -*-

import logging as log

from google.cloud import datastore

import secrets


def dump_data():
    """Dumps the whole dataset to Cloud Datastore"""
    if not empty_dataset():
        import json
        client = datastore.Client()
        key = client.key("Data", 1)
        client.delete(key)

        # Prepares the new entity
        data = datastore.Entity(key=key, exclude_from_indexes=("groups", "users", "drivers"))
        data["groups"] = json.dumps(secrets.groups)
        data["users"] = json.dumps(secrets.users)
        data["drivers"] = json.dumps(secrets.drivers)

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

        secrets.groups = json.loads(data["groups"])
        secrets.users = json.loads(data["users"])
        secrets.drivers = json.loads(data["drivers"])
        return True
    else:
        return False


def print_data():
    """Prints to the Cloud Console Logs the current dataset"""
    client = datastore.Client()
    data = client.get(client.key('Data', 1))
    log.info("Stored data: " + str(data["drivers"]) + str(data["users"]) + str(data["groups"]))
    log.info("Internal data: " + str(secrets.drivers) + str(secrets.users) + str(secrets.groups))


def empty_datastore():
    """Verifies that the Cloud Datastore is empty"""
    return datastore.Client().get(datastore.Client().key("Data", 1)) is None


def empty_dataset():
    """Verifies if the input data from secrets.py is empty"""
    return secrets.groups == {} or secrets.users == {} or secrets.drivers == {}
