import djangosetup
from google.appengine.ext import webapp,db
from google.appengine.ext.webapp.util import run_wsgi_app, login_required
import logging
from django.utils import simplejson
import model
from libs.gsfoid import utils, userlib
import etc
from google.appengine.ext import deferred

# cron jobs

class MidnightPage(utils.RequestHandlerExt):
    def get(self):
        u = model.User()
        u.reset_today_stat()
        self.renderText('All right')

class NewSeasonPage(utils.RequestHandlerExt):
    def get(self):
        # strategy: copy all stat in StatSeason, remove current stat
        # send request to twisted to remove all scores
        u = model.User()
        u.new_season()
        model.Stat.clearStatInTwisted()
        self.renderText('All right')

application = webapp.WSGIApplication(
        [
            ('/cron/midnight', MidnightPage),
            ('/cron/new_season', NewSeasonPage),
        ],
        debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

