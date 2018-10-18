# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import webapp2

from dumpable import dump_data, get_data, print_data


class ScriptHandler(webapp2.RequestHandler):
    def get(self):
        get_data()
        script()
        print_data()
        dump_data()


def script():
    pass
