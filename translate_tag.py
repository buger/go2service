from google.appengine.ext import webapp
from google.appengine.ext import db

import os

from models import *


register = webapp.template.create_template_register()


@register.filter
def i18n(msg_id, hidden_info):
    lang = os.environ['i18n_lang']
    msg = i18nEntry.get_by_key_name(msg_id+os.environ['i18n_lang'])

    if msg is None:
        msg = msg_id
    else:
        msg = msg.data

    if hidden_info:
        msg += "<!--msg_id:"+msg_id+"-->"

    return msg

@register.filter
def cat(str1, str2):
    return str(str1)+str(str2)


@register.filter
def file_url(file_id):
    file_entry = FileEntry.get_by_key_name(file_id)

    if file_entry is None:
        return "/images/empty.gif#file_id="+file_id
    else:
        return file_entry.url+"#file_id="+file_id

