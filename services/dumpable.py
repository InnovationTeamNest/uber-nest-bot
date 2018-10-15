# -*- coding: utf-8 -*-

import sys

from google.cloud import datastore

import secret_data


def dump_data():
    """Dumps the whole dataset to Cloud Datastore"""
    if not empty_dataset():
        import json
        client = datastore.Client()
        key = client.key('Data', 1)
        client.delete(key)

        # Prepares the new entity
        data = datastore.Entity(key=key,
                                exclude_from_indexes=('groups', 'users', 'drivers'))
        data['groups'] = json.dumps(secret_data.groups)
        data['users'] = json.dumps(secret_data.users)
        data['drivers'] = json.dumps(secret_data.drivers)

        # Saves the entity
        client.put(data)
        return True
    else:
        print("Trying to save empty data!", file=sys.stderr)
        return False


def get_data():
    import json
    """Gets the data from Cloud Datastore"""
    if not empty_datastore():
        client = datastore.Client()
        data = client.get(client.key('Data', 1))

        secret_data.groups = json.loads(data['groups'])
        secret_data.users = json.loads(data['users'])
        secret_data.drivers = json.loads(data['drivers'])
        return True
    else:
        return False


def print_data():
    """Prints to the Cloud Console Logs the current dataset"""
    client = datastore.Client()
    data = client.get(client.key('Data', 1))
    print("Stored data: " + str(data['drivers']) + str(data['users']) + str(data['groups']), file=sys.stderr)
    print("Internal data: " + str(secret_data.drivers) + str(secret_data.users) + str(secret_data.groups),
          file=sys.stderr)


def empty_datastore():
    """Verifies that the Cloud Datastore is empty"""
    return datastore.Client().get(datastore.Client().key('Data', 1)) is None


def empty_dataset():
    """Verifies if the input data from secret_data.py is empty"""
    return secret_data.groups == {} or secret_data.users == {} or secret_data.drivers == {}
