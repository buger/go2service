# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.ext.db import polymodel
from google.appengine.api import users

import simplejson as json

from lib.counter import CachedCounter


class JsonProperty(db.Property):
    data_type = db.Text

    def get_value_for_datastore(self, model_instance):
        value = getattr(model_instance, self.name, None)
        return db.Text(json.dumps(value))
    def make_value_from_datastore(self, value):
        return json.loads(value)

def refname_from_key(key):
    return key.name().split('::')[1]

class Ref(db.Expando):
    num_id = db.IntegerProperty();
    name = db.StringProperty()
    ancestors = db.ListProperty(db.Key)
    parents = db.ListProperty(db.Key)
    group = db.BooleanProperty(default = False)
    props = JsonProperty()

    def toJSON(self, full_info = False):
        data = {
            'name'  : self.name,
            'group' : self.group
        }

        if self.is_saved():
            data['id'] = str(self.key())
            data['num_id'] = str(self.num_id)
        else:
            data['id'] = 'new'
            data['num_id'] = 'Новая запись'

        try:
            data['state'] = getattr(self, 'state')
        except:
            pass

        if full_info:
            try:
                parents = [(str(parent), db.get(parent).name) for parent in self.parents]
            except:
                parents = []

            ancestors = [(str(parent), db.get(parent).name) for parent in self.ancestors]

            data['parents'] = parents

            data['props'] = [
                { 'id': 'num_id',   'type': 'static', 'value': data['num_id'], 'locked': True },
                { 'id': 'name',     'type': 'text',   'value': self.name,      'locked': True },
                { 'id': 'parents',  'type': 'links',  'value': parents,        'locked': True },
                { 'id': 'ancestors','type': 'links',  'value': ancestors,      'locked': True }
            ]

            for parent in self.ancestors:
                parent = db.get(parent)

                if parent.props:
                    for prop in parent.props:
                        prop['locked'] = True
                        prop['inherited_from'] = parent.name

                        try:
                            prop['value'] = getattr(self, str(prop['id']))
                        except AttributeError:
                            pass

                        data['props'].append(prop)

            if self.props:
                for prop in self.props:
                    try:
                        prop['value'] = getattr(self, str(prop['id']))
                    except:
                        prop['value'] = ''

                    data['props'].append(prop);


        return data


class RefImport(db.Model):
    columns = JsonProperty()
    blob_key = db.StringProperty()
    root = db.StringProperty()
    state = db.StringProperty(default = "init")
    all_count = db.IntegerProperty(default = 0)
    message = db.TextProperty()

    created_at = db.DateTimeProperty(auto_now_add = True)

    def counter(self):
        return CachedCounter("%s_%s" % (str(self.key()), self.state))

    def incr(self, amount = 1):
        return self.counter().incr(amount)

    @property
    def count(self):
        return self.counter().count



class RefImportItem(Ref):
    parent_name = db.StringProperty()
    ref_import = db.ReferenceProperty(RefImport)
    real_ref = db.ReferenceProperty(Ref)
    state = db.StringProperty()

class Event(db.Model):
    pass

class i18nEntry(db.Model):
    msg_id = db.StringProperty()
    language = db.StringProperty()
    data = db.TextProperty()

class FileEntry(db.Model):
    url = db.StringProperty()


class HistoryEventModelLevel(db.Model):
    date = db.DateTimeProperty(auto_now = True)
    model = db.StringProperty()
    model_id = db.IntegerProperty()
    action = db.StringProperty(['insert', 'update', 'delete'])
    change = JsonProperty()
    changed_by = db.UserProperty()


class Contact(polymodel.PolyModel):
    name = db.StringProperty()
    phones = db.ListProperty(db.PhoneNumber)
    postal_address = db.ListProperty(db.PostalAddress)
    notes = db.TextProperty()
    created_at = db.DateTimeProperty(auto_now_add = True)


class Company(Contact):
    pass


class Person(Contact):
    pass


class UserModel(Contact):
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



class BaseDocument(polymodel.PolyModel):
    created_at = db.DateTimeProperty(auto_now_add = True)
    updated_at = db.DateTimeProperty(auto_now = True)


class Order(BaseDocument):
    CASH = 1
    CASHLESS = 2

    PAY_TYPES = {
        CASH: 'Наличная',
        CASHLESS: 'Безналичная'
    }

    def pay_types(self):
        return Order.PAY_TYPES.items()

    def get_name(self):
        return "Наряд/Заказ №%d" % self.key().id()

    pay_type = db.IntegerProperty(default = CASH)
    arrival = db.DateTimeProperty()
    departure = db.DateTimeProperty()
    roles = db.StringProperty(default = "")
    warranty = db.BooleanProperty(default = False)


class Invoice(BaseDocument):
    PRICE_QUERY = 1
    ADVANCE = 2
    DOCUMENT_WRITTEN = 3
    DOCUMENT_OBTAINED = 4
    CLOSED = 5
    CANCELED = 6

    STATES = {
        PRICE_QUERY: 'Запрос цен',
        ADVANCE: 'Аванс',
        DOCUMENT_WRITTEN: 'Документы выписаны',
        DOCUMENT_OBTAINED: 'Документы переданы',
        CLOSED: 'Закрыта',
        CANCELED: 'Аннулировано'
    }

    def states(self):
        return Invoice.STATES.items()

    def get_name(self):
        return "Счет №%d" % self.key().id()

    bill_date = db.DateTimeProperty()
    state = db.IntegerProperty()
    payed = db.BooleanProperty()
    pay_date = db.DateTimeProperty()


class Document(BaseDocument):
    USER = 1
    INCIDENT = 2
    ONETIME = 3

    TYPES = {
        USER: 'Абонентский',
        INCIDENT: 'Инцидентный',
        ONETIME: 'Разовый'
    }

    def types(self):
        return Document.TYPES.items()

    def get_name(self):
        return "Договор №%d" % self.key().id()

    doc_type = db.IntegerProperty()

    start = db.DateTimeProperty()
    end = db.DateTimeProperty()

    role = db.StringProperty(default = "")

    doc = db.TextProperty()
    scan = db.BlobProperty()


class DocumentContent(db.Expando):
    content_type = db.IntegerProperty()



class Role(db.Model):
    contractor = db.ReferenceProperty(Contact)
    role_type = db.IntegerProperty()


class Issue(db.Model):
    LOG_CHANGES = True

    NEW = 0
    WAITING = 1
    PROCESSING = 2
    DONE = 3
    CLOSED = 4
    DECLINED = 5

    STATES = {
        NEW: u'Создание',
        WAITING: u'В пути',
        PROCESSING: u'Выполняется',
        DONE: u'Выполнено',
        CLOSED: u'Закрыта',
        DECLINED: u'Отменена'
    }

    FIELD_NAMES = {
        'title': u"Тема",
        'text': u"Текст",
        'comment': u"Комментарий",
        'state': u"Состояние",
        'company_name': u'Наименование компании',
        'company_item': u'Объект',
        'company_contact': u'Контактное лицо',
        'contact_phone': u'Телефон контактного лица',
    }

    AUDIT = ['text', 'comment', 'state', 'company_name', 'company_item', 'company_contact', 'contact_phone']

    title = db.StringProperty(default = "")
    text = db.TextProperty(default = "")
    comment = db.TextProperty(default = "")
    state = db.IntegerProperty(default = NEW)
    created_by = db.UserProperty()

    invoice = db.ReferenceProperty(Invoice)
    order = db.ReferenceProperty(Order)
    document = db.ReferenceProperty(Document)

    company_name = db.StringProperty(default = "")
    company_item = db.StringProperty(default = "")
    company_contact = db.StringProperty(default = "")
    contact_phone = db.StringProperty(default = "")

    created_at = db.DateTimeProperty(auto_now_add = True)
    updated_at = db.DateTimeProperty(auto_now = True)

    def url(self):
        if self.is_saved():
            return "/service/issue/%d" % self.key().id()
        else:
            return "/service/issue"

    def states(self):
        new_state = (Issue.NEW, Issue.STATES[Issue.NEW])
        values = Issue.STATES.items()

        if self.is_saved():
            values.remove(new_state)
        else:
            values = [new_state]

        return values

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

                str_arr.append(u"<b>%s</b> с '%s' на '%s'" % (column_name, change[1], change[2]))

        return "<br/>".join(str_arr)

    def latest_change(self):
        change = HistoryEventModelLevel.all().order("-date").filter("model =", "Issue").filter('model_id =', self.key().id()).get()

        return self.format_changes(change)

    def latest_changes(self):
        changes = HistoryEventModelLevel.all().order("-date").filter("model =", "Issue").filter('model_id =', self.key().id()).fetch(10)

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


import datetime
import time

SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)

def model_to_json(model):
    output = {}

    for key, prop in model.properties().iteritems():
        value = getattr(model, key)

        if value is None or isinstance(value, SIMPLE_TYPES):
            output[key] = value
        elif isinstance(value, datetime.date):
            # Convert date/datetime to ms-since-epoch ("new Date()").
            ms = time.mktime(value.utctimetuple()) * 1000
            ms += getattr(value, 'microseconds', 0) / 1000
            output[key] = int(ms)
        elif isinstance(value, db.GeoPt):
            output[key] = {'lat': value.lat, 'lon': value.lon}
        elif isinstance(value, db.Model):
            output[key] = ''#model_to_json(value)
        else:
            raise ValueError('cannot encode ' + repr(prop))

    try:
        output['key'] = str(model.key())
        output['id'] = str(model.key())
        output['num_id'] = str(model.key().id())
    except:
        pass

    try:
        output['count'] = model.count
    except:
        pass

    return output
