#!/usr/bin/env python
import os
import jinja2
import webapp2
import hmac
import hashlib
import time
import datetime
import secret
from models import Task, User

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}

        cookie_value = self.request.cookies.get("uid")

        if cookie_value:
            params["login"] = self.verify_cookie(cookie_value=cookie_value)
        else:
            params["login"] = False

        template = jinja_env.get_template(view_filename)
        return self.response.out.write(template.render(params))

    def create_cookie(self, user):
        user_id = user.key.id()
        expires = datetime.datetime.utcnow() + datetime.timedelta(days=10)
        expires_ts = int(time.mktime(expires.timetuple()))
        code = hmac.new(str(user_id), str(secret) + str(expires_ts), hashlib.sha1).hexdigest()
        value = "{0}:{1}:{2}".format(user_id, code, expires_ts)
        self.response.set_cookie(key="uid", value=value, expires=expires)

    def verify_cookie(self, cookie_value):
        user_id, code, expires_ts = cookie_value.split(":")

        if datetime.datetime.utcfromtimestamp(float(expires_ts)) > datetime.datetime.now():
            verify = hmac.new(str(user_id), str(secret) + str(expires_ts), hashlib.sha1).hexdigest()

            if code == verify:
                return True
            else:
                return False
        else:
            return False

class MainHandler(BaseHandler):
    def get(self):
        return self.render_template("main.html")

class EnterTaskHandler(BaseHandler):
    def post(self):
        name = self.request.get("task_name")
        message = self.request.get("task_message")
        message2 = self.request.get("task_message2")
        checked = bool(self.request.get("task_check"))

        task = Task(name=name, message=message, message2=message2, checked=checked)
        task.put()

        return self.write("You have written: " + "\n" + " name: " + name + " message: " + message + " message2: " +
                          message2 + " check: " + str(checked))

class AllTasksHandler(BaseHandler):
    def get(self):
        tasks = Task.query(Task.deleted == False).fetch()
        params = {'tasks': tasks}
        return self.render_template("all_tasks.html", params=params)

class AllTrueTasksHandler(BaseHandler):
    def get(self):
        tasks = Task.query(Task.deleted == True).fetch();
        params = {'tasks': tasks}
        return self.render_template("all_tasks_t.html", params=params)

class SingleTaskHandler(BaseHandler):
    def get(self, task_id):
        task = Task.get_by_id(int(task_id))
        params = {"task": task}
        return self.render_template("single_task.html", params=params)

class SingleTrueTaskHandler(BaseHandler):
    def get(self, task_id):
        task = Task.get_by_id(int(task_id))
        params = {"task": task}
        return self.render_template("single_true_task.html", params=params)

class EditTaskHandler(BaseHandler):
    def get(self, task_id):
        task = Task.get_by_id(int(task_id))
        params = {"task": task}
        return self.render_template("edit_task.html", params=params)

    def post(self, task_id):
        name = self.request.get("task_name")
        message = self.request.get("task_message")
        message2 = self.request.get("task_message2")
        checked = bool(self.request.get("task_check"))
        task = Task.get_by_id(int(task_id))
        task.name = name
        task.message = message
        task.message2 = message2
        task.checked = checked
        task.put()
        return self.redirect_to("all-tasks")

class EditTrueTaskHandler(BaseHandler):
    def get(self, task_id):
        task = Task.get_by_id(int(task_id))
        params = {"task": task}
        return self.render_template("edit_task_t.html", params=params)

    def post(self, task_id):
        name = self.request.get("task_name_t")
        message = self.request.get("task_message_t")
        message2 = self.request.get("task_message2_t")
        checked = bool(self.request.get("task_check_t"))
        deleted = not(bool(self.request.get("task_delete_t")))
        task = Task.get_by_id(int(task_id))
        task.name = name
        task.message = message
        task.message2 = message2
        task.checked = checked
        task.deleted = deleted
        task.put()
        return self.redirect_to("all-tasks-t")

class DeleteTaskHandler(BaseHandler):
    def get(self, task_id):
        task = Task.get_by_id(int(task_id))
        params = {"task": task}
        return self.render_template("delete_task.html", params=params)

    def post(self, task_id):
        task = Task.get_by_id(int(task_id))
        task.deleted = True
        task.put()
        return self.redirect_to("all-tasks")

class DeleteFinallyTaskHandler(BaseHandler):
    def get(self, task_id):
        task = Task.get_by_id(int(task_id))
        params = {"task": task}
        return self.render_template("delete_task_t.html", params=params)

    def post(self, task_id):
        task = Task.get_by_id(int(task_id))
        task.key.delete()
        return self.redirect_to("all-tasks-t")

class RegistrationHandler(BaseHandler):
    def get(self):
        return self.render_template("registration.html")

    def post(self):
        reg_name = self.request.get("reg_name")
        reg_surname = self.request.get("reg_surname")
        reg_email = self.request.get("reg_email")
        reg_pass = self.request.get("reg_pass")
        reg_pass2 = self.request.get("reg_pass2")

        if reg_pass == reg_pass2:
            User.create(reg_name=reg_name, reg_surname=reg_surname, reg_email=reg_email, orig_password=reg_pass)
            return self.redirect_to("main")

class LoginHandler(BaseHandler):
    def get(self):
        return self.render_template("login.html")

    def post(self):
        log_email = self.request.get("log_email")
        log_password = self.request.get("log_pass")

        user = User.query(User.reg_email == log_email).get()

        if User.verify_pass(orig_password=log_password, user=user):
            #return self.write("User is logged in")
            self.create_cookie(user=user)
            return self.redirect_to("main")
        else:
            return self.write("No no")


app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler, name="main"),
    webapp2.Route('/registration', RegistrationHandler),
    webapp2.Route('/login', LoginHandler),
    webapp2.Route('/tasks', EnterTaskHandler),
    webapp2.Route('/all-tasks', AllTasksHandler, name="all-tasks"),
    webapp2.Route('/all-tasks-t', AllTrueTasksHandler, name="all-tasks-t"),
    webapp2.Route('/single-task/<task_id:\\d+>', SingleTaskHandler),
    webapp2.Route('/single-task-t/<task_id:\\d+>', SingleTrueTaskHandler),
    webapp2.Route('/single-task/<task_id:\\d+>/edit', EditTaskHandler),
    webapp2.Route('/single-task-t/<task_id:\\d+>/edit-finally', EditTrueTaskHandler),
    webapp2.Route('/single-task/<task_id:\\d+>/delete', DeleteTaskHandler),
    webapp2.Route('/single-task-t/<task_id:\\d+>/delete-finally', DeleteFinallyTaskHandler),
], debug=True)

