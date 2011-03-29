from handlers.service import *

class IssueList(ServiceHandler):
    def get(self):
        issues = Issue.all().order("-updated_at")

        self.render_template("service/issues.html", {'issues': issues})

def update_issue(issue, request):
    issue.title = request.get("title")
    issue.text = request.get("text")
    issue.state = int(request.get("state"))

    if request.get("comment") != "":
        issue.comment = request.get("comment")

    issue.put()

    return issue

route('/service/issues', IssueList)


class IssueNew(ServiceHandler):
    def get(self):
        user = users.get_current_user()
        issue = Issue(created_by = user)

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

        self.render_template("service/issue_form.html", {'issue': issue});

    def post(self, issue_id):
        issue = Issue.get_by_id(int(issue_id))
        issue.changed_by = users.get_current_user()

        update_issue(issue, self.request)

        self.redirect("/service/issue/%d" % issue.key().id())
route('/service/issue/:issue_id', IssueEdit)
