from handlers.base import *
import os

class StaticPage(AppHandler):
    def get(self, template = "index.html"):
        try:
            self.render_template(template)
        except:
            self.render_template("404.html")

route('/', StaticPage)
route('/:template', StaticPage)
