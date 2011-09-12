#-*-coding: utf-8 -*-
from google.appengine.ext.webapp import template
from django.utils import simplejson
import math
import datetime
import pytils
from django.utils.safestring import mark_safe
from libs.gsfoid import utils
import logging

register = template.create_template_register()

@register.filter
def score(object, autoescape=None):
    val = int(object)
    if object > 0:
        res = "<font color='green'>+%s</font>" % object
    else:
        res = "<font color='red'>%s</font>" % object
    return mark_safe(res)

@register.filter
def plural_num(object,variants):
    i = int(object)
    return pytils.numeral.get_plural(i, variants)

def get_num_suffix(val):
    val = int(str(val).split('-')[-1])
    if utils.RequestHandlerExt.lang=='ru':
        if val%100!=13 and val%10==3:
            return '-е'
        else:
            return '-ое'
    else:
        # english
        if val%10==1:
            return 'st'
        elif val%10==2:
            return 'nd'
        elif val%10==3:
            return 'rd'
        else:
            return 'th'

@register.filter
def num_suffix_sup(val, autoescape=None):
    return mark_safe(str(val) + '<sup>' + get_num_suffix(val) + '</sup>')

@register.filter
def num_suffix(val, autoescape=None):
    return str(val) + get_num_suffix(val)
