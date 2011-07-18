# -*- coding: utf-8 -*-
from handlers.base import *

class ServiceHandler(AppHandler):
    def render_template(self, name, data = None):
        if data is None:
            data = {}

        try:
            user = UserModel.gql("WHERE user = USER('%s')" % self.session['email']).get()
            data['user'] = user
        except:
            user = None

        data['login_url'] = users.create_login_url("/service")
        data['logout_url'] = users.create_logout_url("/service")

        if not users.is_current_user_admin():
            if user is None:
                return super(ServiceHandler, self).render_template("service/login.html", data)
            else:
                if not user.verified:
                    return super(ServiceHandler, self).render_template("service/wait_for_confirm.html", data)
        else:
            data['user'] = users.get_current_user()

        super(ServiceHandler, self).render_template(name, data)


class ServicePage(ServiceHandler):
    def get(self):
        self.render_template("service/workspace.html")

route('/service', ServicePage)
route('/service/', ServicePage)


class ServiceUsers(ServiceHandler):
    def get(self):
        waiting_users = UserModel.all().filter("verified =", False)
        active_users = UserModel.all().filter("verified =", True)

        self.render_template("service/users.html", { 'waiting_users': waiting_users, 'active_users': active_users})

route('/service/users', ServiceUsers)


class ServiceUser(ServiceHandler):
    def get(self, user_id):
        user_model = UserModel.get_by_id(int(user_id))

        self.render_template("service/edit_user.html", { 'user_model': user_model })

    def post(self, user_id):
        user_model = UserModel.get_by_id(int(user_id))

        roles = self.request.get_all('roles[]')
        roles = map(int, roles)

        user_model.roles = roles
        user_model.put()

        self.redirect('/service/users')

route('/service/user/:user_id', ServiceUser)



class ServiceActivateUser(ServiceHandler):
    def get(self, user_id):
        user_model = UserModel.get_by_id(int(user_id))
        user_model.verified = True
        user_model.put()

        title = "Подтвержение регистрации"
        body = u"""
            Ваш аккаунт подтвержден. Вы можете войти в систему в систему по этой <a href='go2service.appspot.com/service'>ссылке</a>
        """

        mail.send_mail("vadim@go2service.ru", user_model.user.email(), title, body)

        self.redirect('/service/users')

route('/service/user/activate/:user_id', ServiceActivateUser)

import random

from handlers.google_calendar import *

class MyService(AppHandler):
    def get(self):
        if self.session['logged']:
            data = {
                'company': self.session['company'],
                'object': self.session['object'],
                'address': self.session['address'],
                'contact': self.session['contact'],
                'phone': self.session['phone'],
                'email': self.session['email']
            }
        else:
            data = {}

        data['issue_id'] = random.randint(1000, 9999)

        self.render_template("my.html", {'data': data} )

    def post(self):
        title = u"Заявка №%s" % self.request.get('issue_id')
        body = u"""
            Заявка: %s
            Должность, ФИО контактного лица: %s
            Телефон контактного лица: %s
            Юридическое назване клиента: %s

            Название объекта: %s
            Тип объекта: %s
            Адрес объекта: %s
            Должность, ФИО ответственного лица на объекте: %s

            Тип оборудования: %s
            Производитель оборудования: %s
            Марка оборудования: %s
            Модель оборудования: %s

            Дата приема заявки на обслуживание: %s
            Текст заявки: %s
            Ожидаемое время исполнения заявки: %s
        """ % (self.request.get('issue_id'),
               self.request.get('contact'),
               self.request.get('phone'),
               self.request.get('company'),
               self.request.get('object_name'),
               self.request.get('object_type'),
               self.request.get('object_address'),
               self.request.get('object_contact'),
               self.request.get('device_type'),
               self.request.get('device_manufactorer'),
               self.request.get('device_brand'),
               self.request.get('device_model'),
               self.request.get('date'),
               self.request.get('text'),
               self.request.get('estimate')
               )

        mail.send_mail("vadim@go2service.ru", "srv@go2service.ru", title, body)

        try:
            client = gdata.calendar.client.CalendarClient()

            token = pickle.loads(GoogleDataAuth.all().get().token)

            client.auth_token = token
            InsertSingleEvent(client, title, body, self.request.get('company'))
        except:
            pass

        self.session['flash'] = u"Ваша заявка принята!"
        self.session['email'] = self.request.get('email')
        self.session['company'] = self.request.get('company')
        self.session['contact'] = self.request.get('contact')
        self.session['phone'] = self.request.get('phone')

        if self.session['logged']:
            self.redirect('/my')
        else:
            self.redirect('/register')


route('/my', MyService)


class RedirectToMy(AppHandler):
    def get(self):
        self.redirect('http://www.go2service.ru/my')

route('/', RedirectToMy, 'my')


class Register(AppHandler):
    def show_error(self, message):
            self.session['flash'] = message
            self.redirect('/register')

    def get(self):
        self.render_template("register.html")

    def post(self):
        if UserModel.gql("WHERE user = USER('%s')" % self.request.get('email')).get():
            return self.show_error(u"Такой пользователь уже существует!")

        user = UserModel()
        user.set_password(self.request.get('password'))
        user.set_email(self.request.get('email'))
        user.put()

        mail.send_mail("vadim@go2service.ru", self.request.get('email'), u"Регистрация на ксервису.рф", u"Вы зарегистрировались на сайте http://go2service.ru\nДанные для входа:\nАдрес электронной почты: %s\nПароль: %s" % (self.request.get('email'), self.request.get('password')))

        self.session['logged'] = self.request.get('email')
        self.session['email'] = self.request.get('email')

        self.redirect('/my')


route('/register', Register)


class Logout(AppHandler):
    def get(self):
        try:
            del self.session['logged']
        except:
            pass

        self.redirect('/my')

route('/logout', Logout)


class Login(AppHandler):
    def show_error(self, message):
            self.session['flash'] = message
            self.redirect('/login')

    def get(self):
        self.render_template("login.html")

    def post(self):
        user = UserModel.gql("WHERE user = USER('%s')" % self.request.get('email')).get()

        if user:
            if user.check_password(self.request.get('password')):
                self.session['logged'] = self.request.get('email')
                self.session['email'] = self.request.get('email')

                self.redirect('/my')
            else:
                return self.show_error(u"Неправильный пароль!")
        else:
            return self.show_error(u"Пользователь не найден!")


route('/login', Login)


class StealJS(AppHandler):
    def get(self):
        self.render_template("service/stealjs.html")

route('/service/stealjs', StealJS)

