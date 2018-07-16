# -*- coding: utf-8 -*-

import secrets
import google.appengine.ext.ndb as ndb
import logging as log


class Dumpable(ndb.Model):
    groups_morning = ndb.JsonProperty()
    groups_evening = ndb.JsonProperty()
    times_morning = ndb.JsonProperty()
    times_evening = ndb.JsonProperty()
    users = ndb.JsonProperty()
    drivers = ndb.JsonProperty()


class LastKey():
    key = None


def dump_data():
    if LastKey.key is not None:
        LastKey.key.delete()
    if not empty_datastore():
        list_of_keys = Dumpable.query().fetch(keys_only=True)
        for i in list_of_keys:
            i.delete()
        log.info("Error: duplicate data")
    LastKey.key = Dumpable(groups_morning=secrets.groups_morning,
                           groups_evening=secrets.groups_evening,
                           times_morning=secrets.times_morning,
                           times_evening=secrets.times_evening,
                           users=secrets.users,
                           drivers=secrets.drivers).put()


def get_data():
    if LastKey.key is not None and not empty_datastore():
        data = Dumpable.query().fetch()[0]
        secrets.groups_morning = data.groups_morning
        secrets.groups_evening = data.groups_evening
        secrets.times_morning = data.times_morning
        secrets.times_evening = data.times_evening
        secrets.users = data.users
        secrets.drivers = data.drivers


def empty_datastore():
    return Dumpable.query().fetch() is None


def print_data():
    data = Dumpable.query().fetch()[0]
    log.info(data)
