# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import users

import simplejson as json

class JsonProperty(db.Property):
    def get_value_for_datastore(self, model_instance):
        value = getattr(model_instance, self.name, None)
        return json.dumps(value)
    def make_value_from_datastore(self, value):
        return json.loads(value)


class i18nEntry(db.Model):
    msg_id = db.StringProperty()
    language = db.StringProperty()
    data = db.TextProperty()

class FileEntry(db.Model):
    url = db.StringProperty()

class UserModel(db.Model):
    WORKER_ROLE = 1
    ADMIN_ROLE = 2

    ROLE_NAMES = {
        1: 'Управление заявками',
        2: 'Управление пользователями'
    }

    user = db.UserProperty()
    verified = db.BooleanProperty(default = False)
    roles = db.ListProperty(int)

    def is_admin(self):
        return self.roles.count(UserModel.ADMIN_ROLE) == 1

    def is_worker(self):
        return self.roles.count(UserModel.WORKER_ROLE) == 1

    def roles_string(self):
        str_arr = []

        for role in self.roles:
            str_arr.append(UserModel.ROLE_NAMES[role])

        return ','.join(str_arr)


class HistoryEventModelLevel(db.Model):
    date = db.DateTimeProperty(auto_now = True)
    model = db.StringProperty()
    model_id = db.IntegerProperty()
    action = db.StringProperty(['insert', 'update', 'delete'])
    change = JsonProperty()
    changed_by = db.UserProperty()


class Issue(db.Model):
    LOG_CHANGES = True

    NEW = 0
    WAITING = 1
    PROCESSING = 2
    DONE = 3
    DECLINE = 4

    STATES = {
        NEW: u'Создание',
        WAITING: u'На рассмотрении',
        PROCESSING: u'Выполняется',
        DONE: u'Выполнена',
        DECLINE: u'Отменена'
    }

    FIELD_NAMES = {
        'title': u"Тема",
        'text': u"Текст",
        'comment': u"Комментарий",
        'state': u"Состояние"
    }

    AUDIT = ['title', 'text', 'comment', 'state']

    title = db.StringProperty(default = "")
    text = db.TextProperty(default = "")
    comment = db.TextProperty(default = "")
    state = db.IntegerProperty(default = NEW)
    created_by = db.UserProperty()

    created_at = db.DateTimeProperty(auto_now_add = True)
    updated_at = db.DateTimeProperty(auto_now = True)

    def url(self):
        if self.is_saved():
            return "/service/issue/%d" % self.key().id()
        else:
            return "/service/issue"

    def states(self):
        return Issue.STATES.items()

    def state_name(self):
        return Issue.STATES[self.state]

    def format_changes(self, changes):
        str_arr = []

        for change in changes.change:
            if change[0] == "comment":
                str_arr.append(u"Пользователь '%s' добавил комментарий '%s'" % (changes.changed_by.email(), change[2]))
            else:
                title = u"Пользователь '%s' внес изменения:"
                title = title % changes.changed_by.email()
                str_arr.append(title)

                column_name = Issue.FIELD_NAMES[change[0]]
                if change[0] == "state":
                    change[1] = Issue.STATES[int(change[1])]
                    change[2] = Issue.STATES[int(change[2])]

                str_arr.append(u"Измененно значение '%s' с '%s' на '%s'" % (column_name, change[1], change[2]))

        return "<br/>".join(str_arr)

    def latest_change(self):
        change = HistoryEventModelLevel.all().order("-date").filter("model =", "Issue").filter('model_id =', self.key().id()).get()

        return self.format_changes(change)

    def latest_changes(self):
        changes = HistoryEventModelLevel.all().order("-date").filter('model_id =', self.key().id()).filter("model =", "Issue").fetch(10)

        formatted_changes = []
        for change in changes:
            formatted_changes.append(self.format_changes(change))

        return formatted_changes




from google.appengine.api import apiproxy_stub_map
import datetime

def patch_appengine():
    def model_name_from_key(key):
        return key.path().element_list()[0].type()

    def id_from_key(key):
        return key.path().element_list()[0].id()

    def entity_type_from_key(key):
        return eval(model_name_from_key(key))

    def entity_from_key(key):
        return entity_type(key).get_by_id(id_from_key(key))

    def hook(service, call, request, response):
        assert service == 'datastore_v3'
        if call == 'Put':
            for entity in request.entity_list():
                if id_from_key(entity.key()) != 0:
                    entity_type = entity_type_from_key(entity.key())

                    try:
                        fields_for_audit = entity_type.__getattribute__(entity_type,'AUDIT')
                    except:
                        return True

                    db_entity = entity_type.get_by_id(id_from_key(entity.key()))

                    history = HistoryEventModelLevel(action='update', model = entity_type.__name__, changed_by = users.get_current_user(), model_id = db_entity.key().id())

                    def get_name(obj):
                        return obj.name()

                    def get_changes(proplist):
                        changes = []

                        for prop in proplist:
                            if fields_for_audit.count(prop.name()) != 0:
                                db_value = db_entity.__getattribute__(prop.name())

                                if prop.value().has_int64value():
                                    value = str(prop.value().int64value())
                                    db_value = str(db_value)
                                elif prop.value().has_stringvalue():
                                    value = prop.value().stringvalue().decode('utf-8')
                                else:
                                    raise StandardError, prop


                                if db_value != value:
                                    changes.append((prop.name(), db_value, value))

                        return changes

                    prop_changes = get_changes(entity.property_list())
                    for change in get_changes(entity.raw_property_list()):
                        prop_changes.append(change)

                    if len(prop_changes) != 0:
                        history.change = prop_changes
                        history.put()

    apiproxy_stub_map.apiproxy.GetPreCallHooks().Append('preput',hook,'datastore_v3')

patch_appengine()
