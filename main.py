# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import webapp2

import secret_data
from services.dumpable import DataHandler
from services.local_scripts import ScriptHandler
from services.night import NightHandler, WeeklyReportHandler
from services.reminders import ReminderHandler
from webhook import WebHookHandler, UpdateHandler


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("Uber Nest Bot is running!")


app = webapp2.WSGIApplication([
    ("/", MainHandler),
    ("/scripts/localscripts", ScriptHandler),  # local_scripts.py
    ("/scripts/data", DataHandler),  # dumpable.py
    ("/scripts/money", NightHandler),  # night.py
    ("/scripts/weekly_report", WeeklyReportHandler),  # night.py
    ("/scripts/reminders", ReminderHandler),  # reminders.py
    ("/scripts/set_webhook", WebHookHandler),  # webhook.py
    ("/" + secret_data.bot_token, UpdateHandler)  # webhook.py
], debug=True)
