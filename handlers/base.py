import re
import os
import random
import md5
import urllib
import logging

import simplejson as json

from lib.models import *
from lib.counter import *
from lib.lilcookies import *

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import mail

template.register_template_library('with_tag')
template.register_template_library('media_tag')

import copy

cookie_secret = 'af8559a6788b1ee9fbe34307bc1ac39caf8559a6788b1ee9fbe34307bc1ac39c'

class Session:
    def __init__(self, handler):
        self.cookieutil = LilCookies(handler, cookie_secret)

    @property
    def data(self):
        try:
            return self._data
        except:
            try:
                self._data = json.loads(self.cookieutil.get_secure_cookie('data'))
            except:
                self._data = {}

            return self._data

    def __getitem__(self, name):
        try:
            return self.data[name]
        except:
            return ''

    def __setitem__(self, name, value):
        self.data[name] = value
        self.cookieutil.set_secure_cookie('data', json.dumps(self.data))

        return value

    def __delitem__(self, name):
        del self.data[name]

        self.cookieutil.set_secure_cookie('data', json.dumps(self.data))



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

        data['session'] = self.session

        html = template.render(path, data)

        if not data.has_key('dont_render'):
            self.response.out.write(html)

        try:
            del self.session['flash']
        except:
            pass

        return html


    def render_json(self, data):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(data))

    def render_text(self, string):
        self.response.out.write(string)

    # Example:
    #   self.session['data']
    #   self.session['data'] = 'adasdasd'
    #   del self.session['data']
    #
    # Using Flash:
    #   self.session['flash'] = 'asdasd']
    #   self.session['flash'] <- After getting it deletes 'flash' key
    @property
    def session(self):
        try:
            return self._session
        except AttributeError:
            self._session = Session(self)
            return self._session


def throw(obj):
    raise StandardError, obj


routes = {}

def route(string, handler, subdomain = 'www'):
    if subdomain not in routes:
        routes[subdomain] = []

    # convert /edit/:user_id to /edit/([^/]+)?
    string = re.sub("\:([^/]+)?", '([^/]+)?', string)
    routes[subdomain].append([string, handler])

def start():
    if 'HTTP_HOST' in os.environ:
        http_full_host = os.environ['HTTP_HOST']
    else:
        http_full_host = 'localhost'

    subdomain = re.match("(\w+)\.", http_full_host)

    app_routes = []

    if subdomain is None:
        for k,v in routes.items():
            for r in v:
                app_routes.append(r)
    else:
        subdomain = subdomain.group(1)

        if subdomain in routes:
            for r in routes[subdomain]:
                app_routes.append(r)

    application = webapp.WSGIApplication(app_routes, debug=True)
    run_wsgi_app(application)

class Devnull(AppHandler):
    def get(self):
        self.error(200)

    def post(self):
        self.get()

route('/devnull', Devnull)
