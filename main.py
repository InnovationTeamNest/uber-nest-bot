# -*- coding: utf-8 -*-

import webapp2
from webhook import WebHookHandler, UpdateHandler
from secrets import bot_token


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Uber Nest Bot is running!')


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/set_webhook', WebHookHandler),
    ('/' + bot_token, UpdateHandler)
], debug=True)
