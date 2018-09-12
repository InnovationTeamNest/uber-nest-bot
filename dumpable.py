# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging as log

import google.appengine.ext.ndb as ndb

import secret_data


class Dumpable(ndb.Model):
    groups = ndb.JsonProperty()
    users = ndb.JsonProperty()
    drivers = ndb.JsonProperty()
    # datetime = ndb.DateTimeProperty()


def dump_data():
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
    if not empty_datastore():
        data = Dumpable.query().fetch()[0]
        secret_data.groups = data.groups
        secret_data.users = data.users
        secret_data.drivers = data.drivers


def empty_datastore():
    return Dumpable.query().fetch() is None


def empty_dataset():
    return secret_data.groups == {} or secret_data.users == {} or secret_data.drivers == {}


def print_data():
    data = Dumpable.query().fetch()[0]
    print "Stored data: ", data.drivers, data.users, data.groups
    print "Internal data: ", secret_data.drivers, secret_data.users, secret_data.groups
