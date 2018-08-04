# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import secret_data
import google.appengine.ext.ndb as ndb
import logging as log


class Dumpable(ndb.Model):
    groups = ndb.JsonProperty()
    users = ndb.JsonProperty()
    drivers = ndb.JsonProperty()


class LastKey:
    key = None


def dump_data():
    if LastKey.key is not None:
        LastKey.key.delete()
    if not empty_datastore():
        list_of_keys = Dumpable.query().fetch(keys_only=True)
        for i in list_of_keys:
            i.delete()
    LastKey.key = Dumpable(groups=secret_data.groups, users=secret_data.users, drivers=secret_data.drivers).put()


"""
def get_data():
    log.critical("Entering get_data")
    if LastKey.key is not None and not empty_datastore():
        data = Dumpable.query().fetch()[0]
        secrets.groups = data.groups
        secrets.users = data.users
        secrets.drivers = data.drivers
"""


def empty_datastore():
    return Dumpable.query().fetch() is None


def print_data():
    data = Dumpable.query().fetch()[0]
    log.debug(data)
