# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import webapp2
import money
import dumpable
import reminders

from webhook import WebHookHandler, UpdateHandler
from secret_data import bot_token


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("Uber Nest Bot is running!")


class DataHandler(webapp2.RequestHandler):
    def get(self):
        dumpable.print_data()
        self.response.write("Data output in console.")


class MoneyHandler(webapp2.RequestHandler):
    def get(self):
        money.process_debits()
        dumpable.dump_data()
        self.response.write("See console for output.")


class ReminderHandler(webapp2.RequestHandler):
    def get(self):
        reminders.remind()
        self.response.write("See console for output.")


app = webapp2.WSGIApplication([
    ("/", MainHandler),
    ("/data", DataHandler),
    ("/money", MoneyHandler),
    ("/reminders", ReminderHandler),
    ("/set_webhook", WebHookHandler),
    ("/" + bot_token, UpdateHandler)
], debug=True)
