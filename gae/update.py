import djangosetup
from google.appengine.ext import webapp,db
from google.appengine.ext.webapp.util import run_wsgi_app, login_required
import logging
from django.utils import simplejson
from libs.gsfoid import utils, userlib
import etc
from model import *

"""
Template for writing appengine's data store migrations
"""

class UpdatePage(utils.RequestHandlerExt):
    def get(self):
        q = User.all().order('-score')
        i = 0
        if self.request.get('counter'):
            i = int(self.request.get('counter'))
        cursor = None
        if self.request.get('cursor'):
            cursor = self.request.get('cursor')
        q.with_cursor(cursor)
        usp = None
        for u in q.fetch(300):
            if u.score == 0:
                self.renderText('happy end')
                return
            if usp:
                if u.score!=usp.score:
                    usp.put()
                    usp = UserStatPlace.all().filter('score =', u.score).get()
            else:
                usp = UserStatPlace.all().filter('score =', u.score).get()
            if not usp:
                usp = UserStatPlace()
                usp.score = u.score
                usp.count = 1
                usp.place = 0
            else:
                usp.count += 1
            self.renderText("updated:%s score:%s count:%s<br/>" % (i, usp.score, usp.count) )
            i += 1
        if not usp.is_saved():
            usp.put()
        cursor = q.cursor()
        q.with_cursor(cursor)
        if q.count(1) == 0:
            self.renderText('HAPPY END')
        else:
            self.renderText('<script>document.location="/update?cursor=%s&counter=%s";</script>' % (cursor, i) )


application = webapp.WSGIApplication(
        [
            ('/update', UpdatePage),
        ],
        debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
