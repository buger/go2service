# -*- coding: utf-8 -*-
from handlers.base import *

class ServiceHandler(AppHandler):
    def render_template(self, name, data = None):
        if data is None:
            data = {}

        data['user'] = users.get_current_user()
        data['login_url'] = users.create_login_url("/service")
        data['logout_url'] = users.create_logout_url("/service")

        super(ServiceHandler, self).render_template(name, data)


class ServicePage(ServiceHandler):
    def get(self):
        user = users.get_current_user()

        if user is None:
            self.render_template("service/login.html");
        else:
            if users.is_current_user_admin():
                return self.render_template("service/workspace.html")

            user_model = UserModel.all().filter("user =", user).get()

            if user_model is None:
                user_model = UserModel(user = user)
                user_model.put()

            if user_model.verified:
                self.render_template("service/workspace.html")
            else:
                self.render_template("service/wait_for_confirm.html")

route('/service', ServicePage)


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
