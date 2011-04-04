import re, string
from django.template import Node
from google.appengine.ext import webapp

register = webapp.template.create_template_register()

class WithNode(Node):
	def __init__(self, var, name, nodelist):
		self.var = var
		self.name = name
		self.nodelist = nodelist

	def render(self, context):
		val = self.var.resolve(context)
		context.push()
		context[self.name] = val
		output = self.nodelist.render(context)
		context.pop()
		return output

#@register.tag
def do_with(parser, token):
	bits = list(token.split_contents())
	if len(bits) != 4 or bits[2] != "as":
	    raise TemplateSyntaxError, "%r expected format is 'value as name'" % tagname
	var = parser.compile_filter(bits[1])
	name = bits[3]
	nodelist = parser.parse(('endwith',))
	parser.delete_first_token()
	return WithNode(var, name, nodelist)

do_with = register.tag('with', do_with)
