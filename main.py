# -*- coding: utf-8 -*-

import webapp2
import dumpable

from webhook import WebHookHandler, UpdateHandler
from secrets import bot_token


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Uber Nest Bot is running!')


class DumpData(webapp2.RequestHandler):
    def get(self):
        dumpable.print_data()
        self.response.write('Data output in console.')


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/data', DumpData),
    ('/set_webhook', WebHookHandler),
    ('/' + bot_token, UpdateHandler)
], debug=True)
