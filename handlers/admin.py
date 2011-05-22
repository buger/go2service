from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.api import images

import re

from google.appengine.ext.webapp import blobstore_handlers

from handlers.base import *

class AdminPage(AppHandler):
    def get(self):
        self.render_template("index.html")

route('/admin', AdminPage)


class AdminUpdate(AppHandler):
    def post(self):
        language = self.request.get('language')
        messages = json.loads(self.request.get('messages'))
        files = json.loads(self.request.get('files'))

        memcache.delete('home_page_'+language)

        for key, msg in messages.items():
            key_name = key+language

            msg_db = i18nEntry.get_by_key_name(key_name)

            if msg_db is None:
                msg_db = i18nEntry(key_name = key_name,
                                   msg_id = key,
                                   data = msg,
                                   language = language)
            else:
                msg_db.data = msg

            msg_db.put()


        for key, url in files.items():
            key_name = key

            file_db = FileEntry.get_by_key_name(key_name)

            if file_db is None:
                file_db = FileEntry(key_name = key_name,
                                    url = url)
            else:
                file_db.url = url

            file_db.put()

        self.render_json({'success': 'true'})

route('/admin/update', AdminUpdate)


class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blob_key):
        blob_key = str(urllib.unquote(blob_key))

        if not blobstore.get(blob_key):
            self.error(404)
        else:
            if self.request.headers.has_key('If-Modified-Since'):
                self.response.headers["Content-Type"] = blobstore.BlobInfo.get(blob_key).content_type
                self.response.headers["Cache-Control"] = "public, max-age=315360000"
                self.error(304)
            else:
                self.response.headers['Last-Modified'] = "Wed, 26 May 1987 21:21:54 GMT"
                self.response.headers.add_header("Expires", "Thu, 01 Dec 2021 16:00:00 GMT")
                self.response.headers["Cache-Control"] = "public, max-age=315360000"

                self.send_blob(blobstore.BlobInfo.get(blob_key), save_as=True)
route('/media/:blob_key', ServeHandler)


re_image = re.compile('image\/')

class MediaListHandler(AppHandler):
    def get(self):
        json = []

        media_type = self.request.get('type')

        for b in blobstore.BlobInfo.all().order('creation'):
            if media_type == 'image':
                if re_image.match(b.content_type):
                    data = blobstore.fetch_data(b.key(), 0, 50000)
                    image = images.Image(image_data = data)

                    json.append({ 'src': str(b.key()), 'filename': b.filename, 'width': image.width, 'height': image.height})
            else:
                if not re_image.match(b.content_type):
                    json.append({ 'src': str(b.key()), 'filename': b.filename})

        self.render_json(json)
route('/admin/list_media', MediaListHandler)
