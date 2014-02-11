import os
import webapp2
import jinja2
import json
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

def render_str(template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

class Blog(db.Model):
	title = db.StringProperty(required = True)
	entry = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_modified = db.DateTimeProperty(auto_now = True)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		return render_str(template, **params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def render_json(self, d):
		json_txt = json.dumps(d)
		self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
		self.response.out.write(json_txt)

class FinalPage(Handler):
	def get(self, blog_id):
		s = Blog.get_by_id(int(blog_id))
		blogs = db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC")
		if self.request.url.endswith('.json'):
			self.format = 'json'
		else:
			self.format = 'html'
		if self.format == 'html':
			self.render("blogpage.html", blogs=s)
		else:
			tm_fmt = '%c'
			d = {'subject':s.title, 'content':s.entry, 'created':s.created.strftime(tm_fmt), 
					'last_modified':s.last_modified.strftime(tm_fmt)}
			self.render_json([d])
	
class FormPage(Handler):
	def render_form(self, title="", entry="", error=""):
		self.render("form.html", title=title, entry=entry, error = error)

	def get(self):
		self.render("form.html")	

	def post(self):
		title = self.request.get("subject")
		entry = self.request.get("content")
		if title and entry:
			a = Blog(title = title, entry = entry)
			a.put()
			self.redirect("/blog/newpost/%d"%a.key().id())
		else:
			error = "we need both subject and content"
			self.render_form(error = error)


class FrontPage(Handler):
	def get(self):
		blogs = db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC limit 10")
		blogs = list(blogs)
		if self.request.url.endswith('.json'):
			self.format = 'json'
		else:
			self.format = 'html'
		if self.format == 'html':
			self.render("frontpage.html", blogs = blogs)
		else:
			json_str = []
			for blog in blogs:
				tm_fmt = '%c'
				d = {'subject':blog.title, 'content':blog.entry, 'created':blog.created.strftime(tm_fmt), 
					'last_modified':blog.last_modified.strftime(tm_fmt)}
				#json_str.append(d)
				self.render_json(d)

class MainPage(Handler):
	def get(self):
		self.write('Hello udacity')
		
		
app = webapp2.WSGIApplication([ ('/', MainPage),
	                            ('/blog/?(?:\.json)?', FrontPage),
                                ('/blog/newpost', FormPage),
                                ('/blog/newentry/.json', FinalPage),
                                ('/blog/newpost/(\d+)', FinalPage)], 
                                debug=True)