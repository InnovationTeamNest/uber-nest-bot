# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import webapp2

import secret_data
from services.dumpable import DataHandler
from services.money import MoneyHandler, WeeklyReportHandler
from services.reminders import ReminderHandler
from webhook import WebHookHandler, UpdateHandler


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("Uber Nest Bot is running!")


app = webapp2.WSGIApplication([
    ("/", MainHandler),
    ("/data", DataHandler),  # dumpable.py
    ("/money", MoneyHandler),  # money.py
    ("/weekly_report", WeeklyReportHandler),  # money.py
    ("/reminders", ReminderHandler),  # reminders.py
    ("/set_webhook", WebHookHandler),  # webhook.py
    ("/" + secret_data.bot_token, UpdateHandler)  # webhook.py
], debug=True)
