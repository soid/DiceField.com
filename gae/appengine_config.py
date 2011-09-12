import djangosetup
import sys
import os

sys.path.append("libs/")

if ('SERVER_SOFTWARE' in os.environ) and os.environ['SERVER_SOFTWARE'].startswith('Development'):
    def webapp_add_wsgi_middleware(app):
        from google.appengine.ext.appstats import recording
        app = recording.appstats_wsgi_middleware(app)
        return app

