# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import webapp2

import secret_data
from dumpable import DataHandler
from money import MoneyHandler
from reminders import ReminderHandler
from webhook import WebHookHandler, UpdateHandler


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("Uber Nest Bot is running!")


app = webapp2.WSGIApplication([
    ("/", MainHandler),
    ("/data", DataHandler),  # dumpable.py
    ("/money", MoneyHandler),  # money.py
    ("/reminders", ReminderHandler),  # reminders.py
    ("/set_webhook", WebHookHandler),  # webhook.py
    ("/" + secret_data.bot_token, UpdateHandler)  # webhook.py
], debug=True)
