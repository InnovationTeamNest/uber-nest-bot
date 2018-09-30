# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging as log

import google.appengine.ext.ndb as ndb
import webapp2

import secret_data


class DataHandler(webapp2.RequestHandler):
    """Stampa in console il dataset corrente salvato su secret_data e sul Datastore."""

    def get(self):
        get_data()
        print_data()
        self.response.write("Data output in console.")


class Dumpable(ndb.Model):
    """Classe usata da Datastore per fare il backup dei dati."""
    groups = ndb.JsonProperty()
    users = ndb.JsonProperty()
    drivers = ndb.JsonProperty()


def dump_data():
    """Dumps the whole dataset to Cloud Datastore"""
    if not empty_dataset():
        list_of_keys = Dumpable.query().fetch(keys_only=True)
        for key in list_of_keys:
            key.delete()

        Dumpable(groups=secret_data.groups,
                 users=secret_data.users,
                 drivers=secret_data.drivers).put()
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
