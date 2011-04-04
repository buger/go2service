from handlers.service import *

class DocumentNew(ServiceHandler):
    def get(self):
        pass

    def post(self):
        pass

route('/service/document', DocumentNew)


class DocumentEdit(ServiceHandler):
    def get(self):
        pass

    def post(self):
        pass

route('/service/document/:document_id', DocumentEdit)


class DocumentsList(ServiceHandler):
    def get(self):
        return self.post()
        self.render_template("service/documents.html", {'doc_type':self.request.get('doc_type')})

    def post(self):
        documents = BaseDocument.all().order("-updated_at")
        self.render_template("service/documents.html", {'documents': documents, 'doc_type':self.request.get('doc_type')})

route('/service/documents', DocumentsList)
