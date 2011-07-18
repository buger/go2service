# -*- coding: utf-8 -*-
from handlers.service import *

import pickle

import atom
import gdata.gauth
import gdata.calendar.client

if is_production_mode():
    CONSUMER_KEY = '332251340083.apps.googleusercontent.com'
    CONSUMER_SECRET = 'R5X_Syqh-4LpdbsKq98rpdlW'
else:
    CONSUMER_KEY = '808820664328.apps.googleusercontent.com'
    CONSUMER_SECRET = '_Wvt3GP4Sljr05yvYvrnfcjg'


def get_token():
    if is_production_mode():
        next = 'http://www.go2service.ru/service/calendar/success'
        client_id = "332251340083.apps.googleusercontent.com"
    else:
        client_id = "808820664328.apps.googleusercontent.com"
        next = 'http://localhost:8080/service/calendar/success'

    SCOPES = ['https://www.google.com/calendar/feeds/']

    oauth_callback_url = next

    client = gdata.calendar.client.CalendarClient()

    request_token = client.GetOAuthToken(
    SCOPES, oauth_callback_url, CONSUMER_KEY, consumer_secret=CONSUMER_SECRET)

    gdata.gauth.AeSave(request_token, 'myKey')

    return request_token


class Auth(ServiceHandler):
    def get(self):
        token = get_token()

        self.render_template("service/calendar_auth.html", {'auth_link': token.generate_authorization_url() })

route('/service/calendar/auth', Auth)


def InsertSingleEvent(calendar_client, title='One-time Tennis with Beth',
                      content='Meet for a quick lesson', where='On the courts',
                      start_time=None, end_time=None):
    event = gdata.calendar.data.CalendarEventEntry()
    event.title = atom.data.Title(text=title)
    event.content = atom.data.Content(text=content)
    event.where.append(gdata.calendar.data.CalendarWhere(value=where))

    if start_time is None:
      # Use current time for the start_time and have the event last 1 hour
      start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
      end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(time.time() + 3600))
    event.when.append(gdata.calendar.data.When(start=start_time, end=end_time))

    new_event = calendar_client.InsertEvent(event)

    print 'New single event inserted: %s' % (new_event.id.text,)
    print '\tEvent edit URL: %s' % (new_event.GetEditLink().href,)
    print '\tEvent HTML URL: %s' % (new_event.GetHtmlLink().href,)

    return new_event


class AuthSuccess(ServiceHandler):
    def post(self):
        auth = GoogleDataAuth.all().get()

        if not auth:
            auth = GoogleDataAuth()


        client = gdata.calendar.client.CalendarClient()

        saved_request_token = gdata.gauth.AeLoad('myKey')
        request_token = gdata.gauth.AuthorizeRequestToken(saved_request_token, self.request.uri)
        access_token = client.GetAccessToken(request_token)
        gdata.gauth.AeSave(access_token, 'token')

        auth.token = pickle.dumps(access_token)
        auth.put()

        self.redirect('/service')

    def get(self):
        self.post()

route('/service/calendar/success', AuthSuccess)


class CreateEvent(ServiceHandler):
    def get(self):
        client = gdata.calendar.client.CalendarClient()

        token = pickle.loads(GoogleDataAuth.all().get().token)

        client.auth_token = token
        InsertSingleEvent(client)

route('/service/calendar/create_event', CreateEvent)
