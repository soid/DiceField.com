#-*-coding: utf-8 -*-
import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import datastore_errors,users
from django import forms
from django.utils import simplejson
import logging
import os,random
from google.appengine.api import memcache
from google.appengine.runtime import DeadlineExceededError

from django.utils import translation

class ExceptionJson(Exception):
    pass

def run_in_transaction(method):
    def decorate(*args, **kwds):
        return db.run_in_transaction(method, *args, **kwds)
    return decorate


class RequestHandlerExt(webapp.RequestHandler):
    
    cookies = None
    this_request = None
    
    add_auth = ''
    
    DEV_SERVER = False
    RAND = True

    detect_lang_func = None
    lang = None
    
    def initialize(self, request, response):
        template.register_template_library('libs.gsfoid.templatefilters')
        RequestHandlerExt.cookies = request.cookies
        RequestHandlerExt.this_request = request
        RequestHandlerExt.this_response = response
        
        response.headers.add_header("P3P", 'CP="NOI ADM DEV PSAi COM NAV OUR OTRo STP IND DEM"')

        # detect language
        if RequestHandlerExt.detect_lang_func:
            self.lang = self.detect_lang_func()
            RequestHandlerExt.lang = self.lang
            translation.activate(self.lang)
        else:
            translation.activate('ru')
        
        if os.environ['SERVER_SOFTWARE'].startswith('Development'):
            RequestHandlerExt.DEV_SERVER = True
        else:
            RequestHandlerExt.DEV_SERVER = False
        
        try:
            self.run()
        except AttributeError:
            pass
        super(RequestHandlerExt, self).initialize(request, response)
        
    def handle_exception(self, exception, debug_mode):
        if (type(exception) == ExceptionJson):
            self.response.out.write('{"exception": "' + str(exception) + '"}')
            self.response.set_status(200)
        elif type(exception) == DeadlineExceededError:
            memcache.flush_all()
            self.renderPage('error.html')
            self.response.set_status(500)
        else:
            memcache.flush_all()
            super(RequestHandlerExt, self).handle_exception(exception, debug_mode)
        
    def getRenderPage(self, template_page, vars={}):
        add_vars = {
            'addauth': '&' + self.add_auth,
            'lang': self.lang
        }
        vars.update(add_vars)
        path = os.path.join(os.path.dirname(__file__), '../../templates', template_page)
        return template.render(path, vars)

    def renderPage(self, template_page, vars={}):
        html = self.getRenderPage(template_page, vars)
        self.response.out.write(html)

    def renderJson(self, vars):
        self.response.out.write(simplejson.dumps(vars, ensure_ascii=False))

    def renderText(self, text=''):
        self.response.out.write(text)
        
    def redirect(self, location):
        if self.request.query_string:
            loc = location + '&' + self.add_auth
        else:
            loc = location + '?' + self.add_auth
        super(RequestHandlerExt, self).redirect(loc)

# functions

def option_set(options, name, value):
    if value:
        if not name in options:
            options.append(name)
    else:
        if name in options:
            options.remove(name)
    return options
    

# props
import time,datetime

class EnumProperty(db.Property):
    """
    Maps a list of strings to be saved as int. The property is set or get using
    the string value, but it is stored using its index in the 'choices' list.
    """
    data_type = int

    def __init__(self, choices=None, **kwargs):
        if not isinstance(choices, list):
            raise TypeError('Choices must be a list.')
        super(EnumProperty, self).__init__(choices=choices, **kwargs)

    def get_value_for_datastore(self, model_instance):
        value = self.__get__(model_instance, model_instance.__class__)
        if value not in [None, '']:
            return int(self.choices.index(value))

    def make_value_from_datastore(self, value):
        if value is not None:
            return self.choices[int(value)]

    def empty(self, value):
        return (value is None) or (value=='')

def distr_random(distr):
    s = 0
    for v, p in distr.items():
        s = s + p
    r = random.random() * s
    n = .0
    for v, p in distr.items():
        n = n + p
        if n > r:
            return v

import re
def vkontakte_decode(text):
    return re.sub(r'\\u[0-9a-zA-Z]{4}', lambda s: s.group().decode('unicode-escape'), text)
        
# working with cookie
class Cookie(object):
    
    @staticmethod
    def set(name, value, expired=None):
        cookie = name + "=" + value
        if expired:
            cookie += ';expires=' + str(expired)
        cookie += ";path=/"
        RequestHandlerExt.this_response.headers.add_header("Set-Cookie", cookie)
    
    @staticmethod
    def get(name):
        return RequestHandlerExt.this_request.cookies.get(name, None)
