from google.appengine.ext import webapp
from google.appengine.ext import db

from time import time
import os

register = webapp.template.create_template_register()


@register.filter
def stylesheet(name):
    return "<link rel='stylesheet' type='text/css' href='/css/%s.css?%d'>" % (name, time())

@register.filter
def javascript(name):
    return "<script src='/js/%s.js'></script>" % (name)
