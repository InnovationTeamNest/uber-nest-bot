# -*- coding: utf-8 -*-

import logging as log

from google.cloud import datastore

import secret_data


def dump_data():
    """Dumps the whole dataset to Cloud Datastore"""
    if not empty_dataset():
        list_of_keys = Dumpable.query().fetch(keys_only=True)
        for key in list_of_keys:
            key.delete()


        client = datastore.Client()
        key = client.key('Data', 0)

        # Prepares the new entity
        data = datastore.Entity(key=key)
        data['groups'] = secret_data.groups
        data['users'] = secret_data.users
        data['drivers'] = secret_data.drivers

        # Saves the entity
        client.put(data)
    else:
        log.info("Trying to save empty data!")


def get_data():
    """Gets the data from Cloud Datastore"""
    if not empty_datastore():
        data = Dumpable.query().fetch()[0]
        secret_data.groups = data.groups
        secret_data.users = data.users
        secret_data.drivers = data.drivers


def print_data():
    """Prints to the Cloud Console Logs the current dataset"""
    data = Dumpable.query().fetch()[0]
    log.debug("Stored data: " + str(data.drivers) + str(data.users) + str(data.groups))
    log.debug("Internal data: " + str(secret_data.drivers) + str(secret_data.users) + str(secret_data.groups))


def empty_datastore():
    """Verifies that the Cloud Datastore is empty"""
    return Dumpable.query().fetch() is None


def empty_dataset():
    """Verifies if the input data from secret_data.py is empty"""
    return secret_data.groups == {} or secret_data.users == {} or secret_data.drivers == {}
