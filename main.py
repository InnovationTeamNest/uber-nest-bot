# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import webapp2

import secret_data
from services.dumpable import DataHandler
from services.night import NightHandler, WeeklyReportHandler
from services.reminders import ReminderHandler
from webhook import WebHookHandler, UpdateHandler
from services.local_scripts import ScriptHandler

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("Uber Nest Bot is running!")


app = webapp2.WSGIApplication([
    ("/", MainHandler),
    ("/localscripts", ScriptHandler),  # local_scripts.py
    ("/data", DataHandler),  # dumpable.py
    ("/money", NightHandler),  # night.py
    ("/weekly_report", WeeklyReportHandler),  # night.py
    ("/reminders", ReminderHandler),  # reminders.py
    ("/set_webhook", WebHookHandler),  # webhook.py
    ("/" + secret_data.bot_token, UpdateHandler)  # webhook.py
], debug=True)
