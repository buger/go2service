import re
import os
import random
import md5
import urllib
import logging

import simplejson as json

from lib.models import *
from lib.counter import *

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import mail

template.register_template_library('with_tag')

class AppHandler(webapp.RequestHandler):
    def guess_lang(self):
        lang = self.request.get('lang')

        if lang:
            if lang != 'en' and lang != 'ru':
                lang = 'en'

            os.environ['i18n_lang'] = lang
        else:
            os.environ['i18n_lang'] = 'en'

        return os.environ['i18n_lang']

    def render_template(self, name, data = None):
        self.guess_lang()

        path = os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)),'templates', name))

        if data is None:
            data = {}

        if not data.has_key('admin'):
            data['admin'] = users.is_current_user_admin()

        data['lang'] = os.environ['i18n_lang']

        html = template.render(path, data)

        if not data.has_key('dont_render'):
            self.response.out.write(html)

        return html


    def render_json(self, data):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(data))

    def render_text(self, string):
        self.response.out.write(string)


def throw(obj):
    raise StandardError, obj


routes = []

def route(string, handler):
    # convert /edit/:user_id to /edit/([^/]+)?
    string = re.sub("\:([^/]+)?", '([^/]+)?', string)
    routes.append([string, handler])


def start():
    application = webapp.WSGIApplication(routes, debug=True)
    run_wsgi_app(application)

class Devnull(AppHandler):
    def get(self):
        self.error(200)

    def post(self):
        self.get()

route('/devnull', Devnull)
