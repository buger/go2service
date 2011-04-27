# -*- coding: utf-8 -*-
from handlers.service import *

class RefIndex(ServiceHandler):
    def get(self):
        self.render_template("service/reference.html", {'root': refs})

route('/service/ref', RefIndex)


