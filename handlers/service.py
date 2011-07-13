# -*- coding: utf-8 -*-
from handlers.base import *

class ServiceHandler(AppHandler):
    def render_template(self, name, data = None):
        user = UserModel.gql("WHERE user = USER('%s')" % self.session['email']).get()

        if data is None:
            data = {}

        data['user'] = user
        data['login_url'] = users.create_login_url("/service")
        data['logout_url'] = users.create_logout_url("/service")
        data['production'] = os.environ['SERVER_NAME'] != 'localhost'

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


        self.render_template("my.html", {'data': data} )

    def post(self):
        title = u"Заявка не ремонт оборудования: %s" % self.request.get('company')
        body = u"""
            Юридическое лицо: %s
            Объект: %s
            Адрес места эксплуатации: %s
            Контактное лицо: %s
            Телефонный номер контактного лица: %s
            Адрес электронной почты: %s
            Описание оборудования: %s
            Текст заявки: %s
        """ % (self.request.get('company'),
               self.request.get('object'),
               self.request.get('address'),
               self.request.get('contact'),
               self.request.get('phone'),
               self.request.get('email'),
               self.request.get('description'),
               self.request.get('text'))

        mail.send_mail("vadim@go2service.ru", "srv@go2service.ru", title, body)

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

