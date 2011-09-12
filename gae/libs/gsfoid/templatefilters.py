#-*-coding: utf-8-*-
from google.appengine.ext.webapp import template
from django.utils import simplejson
from django.utils.safestring import mark_safe

register = template.create_template_register()

@register.filter
def jsonify(object):
    res = simplejson.dumps(object, ensure_ascii=False)
    return mark_safe(res)

