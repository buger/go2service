from handlers.base import *

class MainPage(AppHandler):
    def get(self):
        key = "home_page_"+self.guess_lang()
        cache = memcache.get(key)
        cache = None

        if cache:
            self.response.out.write(cache)
        else:
            html = self.render_template("index.html", {'dont_render':True})
            memcache.set(key, html)

            self.response.out.write(html)

route('/', MainPage)
