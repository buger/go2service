from dateutil.parser import *
from handlers.service import *

class IssueList(ServiceHandler):
    def get(self):
        issues = Issue.all().order("-updated_at")

        self.render_template("service/issues.html", {'issues': issues})

route('/service/issues', IssueList)

def update_document(issue, request):
    if request.get("document[_create]"):
        document = Document()
    else:
        document = issue.document

    if request.get("document[start]") != "":
        document.start = parse(request.get("document[start]"))
    else:
        document.start = None

    if request.get("document[end]") != "":
        document.end = parse(request.get("document[end]"))
    else:
        document.end = None


    document.role = request.get("document[role]")
    try:
        document.doc_type = int(request.get("document[doc_type]"))
    except:
        pass

    document.put()

    issue.document = document

def update_invoice(issue, request):
    if request.get("invoice[_create]"):
        invoice = Invoice()
    else:
        invoice = issue.invoice

    if request.get("invoice[bill_date]") != "":
        invoice.bill_date = parse(request.get("invoice[bill_date]"))
    else:
        invoice.bill_date = None

    invoice.payed = request.get("invoice[payed]") != ""

    try:
        invoice.state = int(request.get("invoice[state]"))
    except:
        pass

    invoice.put()

    issue.invoice = invoice


def update_order(issue, request):
    if request.get("order[_create]"):
        order = Order()
    else:
        order = issue.order

    if request.get("order[arrival]") != "":
        order.arrival = parse(request.get("order[arrival]"))
    else:
        order.arrival = None

    if request.get("order[departure]") != "":
        order.departure = parse(request.get("order[departure]"))
    else:
        order.departure = None

    order.roles = request.get("order[roles]")
    order.warranty = request.get("order[warranty]") != ""

    try:
        order.pay_type = int(request.get("order[pay_type]"))
    except:
        pass

    order.put()

    issue.order = order


def update_issue(issue, request):
    issue.title = request.get("title")
    issue.text = request.get("text")

    issue.company_name = request.get("company_name")
    issue.company_item = request.get("company_item")
    issue.company_contact = request.get("company_contact")
    issue.contact_phone = request.get("contact_phone")

    if request.get("comment") != "":
        issue.comment = request.get("comment")

    update_order(issue, request)
    update_invoice(issue, request)
    update_document(issue, request)

    issue.put()

    return issue



class IssueNew(ServiceHandler):
    def get(self):
        user = users.get_current_user()
        issue = Issue(created_by = user)

        key = db.Key.from_path('BaseDocument', 1)
        batch = db.allocate_ids(key, 3)

        new_key = db.Key.from_path('BaseDocument', batch[0])
        issue.invoice = Invoice(key = new_key)

        new_key = db.Key.from_path('BaseDocument', batch[0]+1)
        issue.document = Document(key = new_key)

        new_key = db.Key.from_path('BaseDocument', batch[0]+1)
        issue.order = Order(key = new_key)

        self.render_template("service/issue_form.html", {'issue': issue});

    def post(self):
        user = users.get_current_user()
        issue = Issue(created_by = user, state = Issue.WAITING)
        issue = update_issue(issue, self.request)

        self.redirect("/service/issue/%d" % issue.key().id())

route('/service/issue', IssueNew)


class IssueEdit(ServiceHandler):
    def get(self, issue_id):
        issue = Issue.get_by_id(int(issue_id))

        self.render_template("service/issue_form.html", {'issue': issue})

    def post(self, issue_id):

        self.render_template("service/issue_form.html", {'issue': issue});

    def post(self):
        user = users.get_current_user()
        issue = Issue(created_by = user, state = Issue.WAITING)
        issue = update_issue(issue, self.request)

        self.redirect("/service/issue/%d" % issue.key().id())

route('/service/issue', IssueNew)


class IssueEdit(ServiceHandler):
    def get(self, issue_id):
        issue = Issue.get_by_id(int(issue_id))

        self.render_template("service/issue_form.html", {'issue': issue})

    def post(self, issue_id):

        self.render_template("service/issue_form.html", {'issue': issue});

    def post(self):
        user = users.get_current_user()
        issue = Issue(created_by = user, state = Issue.WAITING)
        issue = update_issue(issue, self.request)

        self.redirect("/service/issue/%d" % issue.key().id())

route('/service/issue', IssueNew)


class IssueEdit(ServiceHandler):
    def get(self, issue_id):
        issue = Issue.get_by_id(int(issue_id))

        self.render_template("service/issue_form.html", {'issue': issue})

    def post(self, issue_id):
        issue = Issue.get_by_id(int(issue_id))
        issue.state = int(self.request.get("state"))

        update_issue(issue, self.request)

        self.redirect("/service/issue/%d" % issue.key().id())

route('/service/issue/:issue_id', IssueEdit)
