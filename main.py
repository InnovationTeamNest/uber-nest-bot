# -*- coding: utf-8 -*-

import webapp2
import money
import dumpable

from webhook import WebHookHandler, UpdateHandler
from secrets import bot_token


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Uber Nest Bot is running!')


class DataHandler(webapp2.RequestHandler):
    def get(self):
        dumpable.print_data()
        self.response.write('Data output in console.')


class MoneyHandler(webapp2.RequestHandler):
    def get(self):
        money.process_debits()
        self.response.write('See console for output.')


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/data', DataHandler),
    ('/money', MoneyHandler),
    ('/set_webhook', WebHookHandler),
    ('/' + bot_token, UpdateHandler)
], debug=True)
