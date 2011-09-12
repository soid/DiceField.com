import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'
from google.appengine.dist import use_library
use_library('django', '1.2')

from django.conf import settings
# Force Django to reload settings
settings._target = None
