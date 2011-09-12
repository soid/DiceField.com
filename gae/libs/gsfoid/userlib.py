#-*-coding: utf-8 -*-
import utils
import logging
import os
from google.appengine.ext import db
from google.appengine.api import users as gusers
import hashlib
import random
from django.utils import simplejson as json
import datetime
import urllib,urllib2
import utils
import locations
import vklib

from django.utils.translation import ugettext as _

class VKUser(db.Model):
    # public
    nickname = db.StringProperty()
    birthday = db.DateProperty()
    sex = utils.EnumProperty(choices=['male', 'female'])
    photo = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

    # app access
    access_friends = False
    is_app_user = db.BooleanProperty(default=True)
    
    # internal
    viewer_id = db.IntegerProperty(default=None)

    # referals
    ref_user_id = db.IntegerProperty(default=None)
    ref_group_id = db.IntegerProperty(default=None)
    ref_viewer_type = db.IntegerProperty(default=None)
    ref_referrer = db.StringProperty(default=None)
    ref_url_ref = db.StringProperty(default=None)

    # location
    loc_country_id = db.IntegerProperty()
    loc_city_id = db.IntegerProperty()
    loc_city = db.StringProperty()

    @staticmethod
    def setup():
        if utils.RequestHandlerExt.DEV_SERVER:
            VKUser.APP_ID = 1928106
            VKUser.SECRET = ''
        else:
            VKUser.APP_ID = 1955838
            VKUser.SECRET = ''

    @staticmethod
    def auth_by_key(request):
        auth_key = request.get('auth_key')
        viewer_id = request.get('viewer_id')
        api_result = request.get('api_result')
        api_settings = request.get('api_settings')

        VKUser.setup()
        md5 = hashlib.md5()
        md5.update('%s_%s_%s' % (VKUser.APP_ID, viewer_id, VKUser.SECRET))
        r = md5.hexdigest()
        if r != auth_key:
            raise Exception('Incorrect authorization auth_key')
        
        viewer_id = int(viewer_id)
        query = db.GqlQuery("SELECT * FROM VKUser WHERE viewer_id=:id", id=viewer_id)
        vkuser = query.get()
        if vkuser is None:
            vkuser = VKUser()
            vkuser.viewer_id = viewer_id
            if request.get('user_id'):
                vkuser.ref_user_id = int(request.get('user_id'))
            if request.get('group_id'):
                vkuser.ref_group_id = int(request.get('group_id'))
            if request.get('viewer_type'):
                vkuser.ref_viewer_type = int(request.get('viewer_type'))
            if request.get('referrer'):
                vkuser.ref_referrer = request.get('referrer')
            for k in request.headers:
                if k.lower() == 'referer':
                    vkuser.ref_url_ref = request.headers[k]
        vkuser.updateFields(api_result)
        vkuser.is_app_user = True
        vkuser.put()
        vkuser.access_friends = (int(api_settings) & 2 == 2)
        return vkuser

    def updateFields(self, api_result):
        # has to register
        if api_result:
            api_result = api_result.encode('utf8')
            profile = json.loads(api_result)
                
            # validate api_result
            flag = ('response' in profile) and (len(profile['response'])>0)
            if not flag:
                raise Exception("Incorrect parameters have been recieved")
                return
            nick = ''
            if 'first_name' in profile['response'][0]:
                nick = nick + profile['response'][0]['first_name']
            if 'nickname' in  profile['response'][0]:
                if nick != '':
                    nick = nick + ' '
                #nick = nick + utils.vkontakte_decode(profile['response'][0]['nickname'])
            if 'last_name' in profile['response'][0]:
                if nick != '':
                    nick = nick + ' '
                nick = nick + profile['response'][0]['last_name']
            if 'sex' in profile['response'][0]:
                sex = profile['response'][0]['sex']
            else:
                sex = None
            if 'bdate' in profile['response'][0]:
                bdate = profile['response'][0]['bdate']
            else:
                bdate = None
            if 'photo_rec' in profile['response'][0]:
                self.photo = profile['response'][0]['photo_rec']
            elif 'photo' in profile['response'][0]:
                self.photo = profile['response'][0]['photo']
            if sex:
                sex = int(sex)
                if sex == 1:
                    sex = 'female'
                elif sex == 2:
                    sex = 'male'
                else:
                    sex = None
            birthday = None
            if bdate:
                bdate_split = bdate.split('.')
                if len(bdate_split) == 3:
                    try:
                        birthday = datetime.date(int(bdate_split[2]), int(bdate_split[1]), int(bdate_split[0]))
                    except ValueError:
                        pass
            if 'country' in profile['response'][0]:
                self.loc_country_id = int(profile['response'][0]['country'])
            if 'city' in profile['response'][0]:
                tmp = int(profile['response'][0]['city'])
                if tmp != self.loc_city_id:
                    self.loc_city_id = tmp
                    # request city name
                    vkr = vklib.VKRequest(VKUser.APP_ID, VKUser.SECRET)
                    url = vkr.request({
                        'method': 'getCities',
                        'cids': self.loc_city_id
                    })
                    resp = urllib.urlopen(url).read()
                    resp = json.loads(resp)
                    if 'response' in resp:
                        if len(resp['response'])>0:
                            self.loc_city = resp['response'][0]['name']
            self.nickname = nick
            self.birthday = birthday
            self.sex = sex

    @staticmethod
    def auth(request, response):
        # already internal authorized
        if request.get('auth_key') and request.get('viewer_id'):
            return VKUser.auth_by_key(request)
        elif utils.Cookie.get('vk_auth_key') and utils.Cookie.get('vk_viewer_id'):
            return VKUser.auth_by_key(utils.Cookie.get('vk_auth_key'), utils.Cookie.get('vk_viewer_id'))
        else:
            raise Exception('Incorrect authorization: no params')

    def get_link(self):
        return 'http://vkontakte.ru/id' + str(self.viewer_id)

    def get_norm_country(self):
        return locations.get_country('vk', self.loc_country_id)

    def get_norm_location(self):
        return self.loc_city

    @staticmethod
    def send_notifications(vkusers, text):
        uids = []
        ret = ''
        for u in vkusers:
            uids.append(str(u.viewer_id))
        if len(uids)>0:
            VKUser.setup()
            vkr = vklib.VKRequest(VKUser.APP_ID, VKUser.SECRET)
            url = vkr.saveNotification(",".join(uids), text)
            resp = urllib.urlopen(url)
            ret = str(resp.read())
            retj = json.loads(ret)
            ids = retj['response'].split(',')
            for u in vkusers:
                if str(u.viewer_id) not in ids:
                    u.is_app_user = False
                    u.put()
        return [ret, ids]

# mail.ru social network (Moi Mir)

class MMNotInstalledException(Exception):
    pass

class MMUser(db.Model):

    MM_APP_ID = ''
    MM_SECRET_KEY = ''
    MM_PRIVATE_KEY = ''

    # public
    nickname = db.StringProperty()
    birthday = db.DateProperty()
    sex = utils.EnumProperty(choices=['male', 'female'])
    photo = db.StringProperty()
    link = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    profile_updated = db.DateTimeProperty(auto_now=True)

    # app access
    access_friends = True
    is_app_user = db.BooleanProperty(default=True)
    
    # internal
    user_id = db.StringProperty(default=None)

    # location
    loc_country = db.StringProperty()
    loc_country_id = db.IntegerProperty()
    loc_city = db.StringProperty()

    # referrers
    ref_url_ref = db.StringProperty(default=None)

    @staticmethod
    def rest_request(req):
        req['app_id'] = MMUser.MM_APP_ID
        req['secure'] = '1'
        keys = req.keys()
        keys.sort()
        params = ''
        for k in keys:
            params = params + k + '=' + req[k]
        md5 = hashlib.md5()
        md5.update(params + MMUser.MM_SECRET_KEY)
        req['sig'] = md5.hexdigest()
        resp = json.load(urllib.urlopen(
            "http://www.appsmail.ru/platform/api?" + urllib.urlencode(req)))
        return resp

    @staticmethod
    def setup():
        # setup keys
        if ('SERVER_SOFTWARE' in os.environ) and os.environ['SERVER_SOFTWARE'].startswith('Development'):
            MMUser.MM_APP_ID = '551727'
            MMUser.MM_SECRET_KEY = ''
            MMUser.MM_PRIVATE_KEY = ''
            logging.info('case1')
        else:
            logging.info('case2')
            MMUser.MM_APP_ID = '553628'
            MMUser.MM_SECRET_KEY = ''
            MMUser.MM_PRIVATE_KEY = ''
    
    @staticmethod
    def auth(request, response):
        if request.get('is_app_user') != '1':
            raise MMNotInstalledException("App not installed")

        MMUser.setup()

        # getting vars
        session_key = request.get('session_key')
        user_id = request.get('vid')
        
        # check signature
        args = request.arguments()
        args.sort()
        params = ''
        for k in args:
            if k not in ['sig', 'fcid']:
                params = params + k + '=' + request.get(k)
        md5 = hashlib.md5()
        md5.update(params + MMUser.MM_SECRET_KEY)
        r = md5.hexdigest()
        if r != request.get('sig'):
            raise Exception("Incorrect authorization")

        query = db.GqlQuery("SELECT * FROM MMUser WHERE user_id=:id", id=user_id)
        user = query.get()
        need_update = user and ((datetime.datetime.now() - user.profile_updated).days>0)

        if (not user) or need_update:
            # extended data request
            res = MMUser.rest_request({'method': 'users.getInfo', 'uids': user_id, 'session_key': session_key})
            logging.info(res)
            res = res[0]
            if not user:
                user = MMUser()
                user.user_id = user_id
                # new user, save referrers
                for k in request.headers:
                    if k.lower() == 'referer':
                        user.ref_url_ref = request.headers[k][-499:]
            nick = ''
            if 'first_name' in res:
                nick = nick + res['first_name']
            if 'last_name' in res:
                nick = nick + ' ' + res['last_name']
            user.nickname = nick
            if 'pic_small' in res:
                user.photo = res['pic_small']
            if 'sex' in res:
                if res['sex'] == 0:
                    user.sex = 'male'
                else:
                    user.sex = 'female'
            if 'birthday' in res:
                bday = res['birthday'].split('.')
                if len(bday) == 3:
                    user.birthday = datetime.date(int(bday[2]), int(bday[1]), int(bday[0]))
            if 'link' in res:
                user.link = res['link']
            if 'location' in res:
                if 'country' in res['location']:
                    user.loc_country_id = int(res['location']['country']['id'])
                    user.loc_country = res['location']['country']['name']
                if 'city' in res['location']:
                    user.loc_city = res['location']['city']['name']
            user.profile_updated = datetime.datetime.now()
            user.put()
        return user
    
    def get_link(self):
        return self.link

    def get_norm_country(self):
        return locations.get_country('mm', self.loc_country_id)

    def get_norm_location(self):
        return self.loc_city

    @staticmethod
    def send_notifications(mmusers, text):
        uids = []
        ret = ''
        for u in mmusers:
            uids.append(str(u.user_id))
        resp = ''
        if len(uids)>0:
            MMUser.setup()
            resp = MMUser.rest_request({
                'method': 'notifications.send',
                'uids': ",".join(uids),
                'text': text
            })
            ids = resp
            for u in mmusers:
                if str(u.user_id) not in ids:
                    u.is_app_user = False
                    u.put()
        return [resp, ids]

## Odnoklassniki.ru ##

class OdnkUser(db.Model):
    APP_ID = ''
    APP_KEY = ''
    APP_SECRET = ''
    
    # fields
    nickname = db.StringProperty()
    birthday = db.DateProperty()
    sex = utils.EnumProperty(choices=['male', 'female'])
    photo = db.StringProperty()
    loc_country = db.StringProperty(default=None)
    loc_city = db.StringProperty(default=None)
    profile_updated = db.DateTimeProperty(auto_now=True)

    # app access
    access_friends = True
    
    # internal
    user_id = db.IntegerProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

    # referers
    ref_url_ref = db.StringProperty(default=None)

    @staticmethod
    def setup():
        if utils.RequestHandlerExt.DEV_SERVER:
            OdnkUser.APP_ID = '431872'
            OdnkUser.APP_KEY = ''
            OdnkUser.APP_SECRET = ''
        else:
            OdnkUser.APP_ID = '431872'
            OdnkUser.APP_KEY = ''
            OdnkUser.APP_SECRET = ''

    @staticmethod
    def rest_request(api_server, session_key, session_secret_key, req):
        req['application_key'] = OdnkUser.APP_KEY
        req['session_key'] = session_key
        req['format'] = 'JSON'

        # calc sig
        keys = req.keys()
        keys.sort()
        params = ''
        for k in keys:
            params = params + k + '=' + str(req[k])
        md5 = hashlib.md5()
        md5.update(params + session_secret_key)
        req['sig'] = md5.hexdigest()
        
        # request
        url = api_server + 'fb.do?' + urllib.urlencode(req)
        resp = json.load(urllib.urlopen(url))
        return resp

    @staticmethod
    def auth(request, response):
        OdnkUser.setup()

        user_id = request.get('logged_user_id')
        session_key = request.get('session_key')
        auth_sig = request.get('auth_sig')

        VKUser.setup()
        md5 = hashlib.md5()
        md5.update('%s%s%s' % (user_id, session_key, OdnkUser.APP_SECRET))
        r = md5.hexdigest()
        if r != auth_sig:
            raise Exception('Incorrect authorization auth_key')
        
        user_id = long(user_id)
        query = db.GqlQuery("SELECT * FROM OdnkUser WHERE user_id=:id", id=user_id)
        user = query.get()
        need_update = user and ((datetime.datetime.now() - user.profile_updated).days>0)

        if (not user) or need_update:
            res = OdnkUser.rest_request(
                request.get('api_server'), request.get('session_key'), request.get('session_secret_key'),
                {
                    'method': 'users.getInfo',
                    'uids': user_id,
                    'fields': 'name,gender,birthday,location,pic_1,url_profile'
                })
            res = res[0]
            logging.info(res)

            if not user:
                user = OdnkUser()
                user.user_id = user_id
                for k in request.headers:
                    if k.lower() == 'referer':
                        user.ref_url_ref = request.headers[k]

            if 'name' in res:
                user.nickname = res['name']
            else:
                raise Exception('No name from provider')
            if 'pic_1' in res:
                user.photo = res['pic_1']
            if 'sex' in res:
                if res['sex'] == 'male':
                    user.sex = 'male'
                else:
                    user.sex = 'female'
            if 'birthday' in res:
                bday = res['birthday'].split('-')
                if len(bday) == 3:
                    user.birthday = datetime.date(int(bday[0]), int(bday[1]), int(bday[2]))
            if 'location' in res:
                if 'country' in res['location']:
                    user.loc_country = res['location']['country']
                if 'city' in res['location']:
                    user.loc_city = res['location']['city']
            user.profile_updated = datetime.datetime.now()
            user.put()

        user.api_server = request.get('api_server')
        user.apiconnection = request.get('apiconnection')

        return user

    def get_link(self):
        return ''

    def get_norm_country(self):
        return locations.get_country('odnk', self.loc_country)

    def get_norm_location(self):
        return self.loc_city

## FB ##

import string,base64
import hmac,hashlib
import time



def b64web_decode(s):
    return base64.b64decode(s.replace('-', '+').replace('_', '/') + '==')

class FBUser(db.Model):
    # public
    nickname = db.StringProperty()
    birthday = db.DateProperty()
    sex = utils.EnumProperty(choices=['male', 'female'])
    link = db.StringProperty()
    access_friends = True

    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    profile_updated = db.DateTimeProperty(auto_now=True)

    # internal
    user_id = db.IntegerProperty(default=None)

    # location
    loc_country = db.StringProperty()
    loc_name = db.StringProperty()

    @staticmethod
    def setup():
        if utils.RequestHandlerExt.DEV_SERVER:
            if utils.RequestHandlerExt.lang == 'ru':
                FBUser.APP_ID = '192838924084451'
                FBUser.APP_SECRET = ''
                FBUser.APP_NAME = 'vkubiki_test'
            else:
                FBUser.APP_ID = '157201637681400'
                FBUser.APP_SECRET = ''
                FBUser.APP_NAME = 'dicefield_test'

        # production below
        elif utils.RequestHandlerExt.lang == 'ru':
            FBUser.APP_ID = '124335497620323'
            FBUser.APP_SECRET = ''
            FBUser.APP_NAME = 'vkubiki'
        else:
            FBUser.APP_ID = '154367061301394'
            FBUser.APP_SECRET = ''
            FBUser.APP_NAME = 'dicefield'

    @staticmethod
    def auth(request, resp):
        FBUser.setup()
        need_auth = False
        code = resp.request.get("code")
        if code:
            request = resp.request.get("signed_request")
            sig,body = request.split('.')

            # check signature
            sig_exp = hmac.new(FBUser.APP_SECRET, body, hashlib.sha256).digest()
            if sig_exp != b64web_decode(sig):
                raise Exception, "Incorrect authorization"

            js = json.loads(b64web_decode(body))
            if 'user_id' in js:
                user_id = int(js['user_id'])

                query = db.GqlQuery("SELECT * FROM FBUser WHERE user_id=:id", id=user_id)
                user = query.get()

                need_update = user and ((datetime.datetime.now() - user.profile_updated).days>0)

                if js['expires']<time.time():
                    # need a new token
                    url = 'https://graph.facebook.com/oauth/access_token?' \
                        + urllib.urlencode({
                            'client_id': FBUser.APP_ID,
                            'redirect_uri': 'http://apps.facebook.com/' + FBUser.APP_NAME + '/',
                            'client_secret': FBUser.APP_SECRET,
                            'code': code
                        })
                    resp.renderPage('fb_redirect.html', {'redirect_url': url})
                    return 'internal_work'
                else:
                    access_token = js['oauth_token']
                    if (not user) or need_update:
                        logging.info(access_token)
                        profile = json.load(urllib2.urlopen(
                            "https://graph.facebook.com/me?" +
                            urllib.urlencode({
                                'fields': 'name,about,link,gender,birthday,location',
                                'access_token': access_token,
                                'locale': 'en_US'
                            })))
                        if not user:
                            user = FBUser()
                            user.user_id = user_id
                        logging.info(profile)
                        user.nickname = profile['name']
                        user.link = profile['link']
                        if 'gender' in profile:
                            if profile['gender'] == 'male':
                                user.sex = 'male'
                            else:
                                user.sex = 'female'
                        if 'birthday' in profile:
                            bday = profile['birthday'].split('/')
                            if len(bday) == 3:
                                user.birthday = datetime.date(int(bday[2]), int(bday[0]), int(bday[1]))
                        user.profile_updated = datetime.datetime.now()

                        # for to get normalized location
                        url = 'https://api.facebook.com/method/fql.query?' + \
                            urllib.urlencode({
                                'query': 'SELECT current_location FROM user WHERE uid=me()',
                                'access_token': access_token,
                                'format': 'json',
                            })
                        ext_info = json.load(urllib2.urlopen(url))
                        ext_info = ext_info[0]
                        logging.info(ext_info)
                        if ('current_location' in ext_info) and (ext_info['current_location']):
                            if 'country' in ext_info['current_location']:
                                user.loc_country = ext_info['current_location']['country']
                            if 'name' in ext_info['current_location']:
                                user.loc_name = ext_info['current_location']['name']

                        user.put()
                    user.access_token = access_token
                    return user
            else:
                need_auth = True
        else:
            need_auth = True

        if need_auth:
            url = 'https://graph.facebook.com/oauth/authorize?' \
                + urllib.urlencode({
                    'client_id': FBUser.APP_ID,
                    'redirect_uri': 'http://apps.facebook.com/' + FBUser.APP_NAME + '/',
                    'scope': 'user_about_me,user_birthday,user_location,friends_online_presence'
                })
            resp.renderPage('fb_redirect.html', {'redirect_url': url})
            return 'internal_work'

    def get_link(self):
        return self.link

    def photo(self):
        return 'http://graph.facebook.com/%s/picture' % self.user_id

    def get_norm_country(self):
        return locations.get_country('fb', self.loc_country)

    def get_norm_location(self):
        return self.loc_name

import genericng
class GuestUser(db.Model):
    # public
    nickname = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    
    token = db.StringProperty()

    @staticmethod
    def auth(request, response):
        c = utils.Cookie.get('guest')
        u = None
        if c:
            u = GuestUser.all().filter('token =', c).get()
        if not u:
            name=GuestUser.gen_name().capitalize()
            u = GuestUser()
            u.nickname = name
            u.token = hashlib.md5(repr(time.time()) + unicode(random.random())).hexdigest()
            u.put()
        d = datetime.datetime.now() + datetime.timedelta(days=21)
        utils.Cookie.set('guest', u.token, time.strftime('%a, %d-%b-%Y %H:%M:%S GMT', d.timetuple()))
        u.access_friends = False
        u.birthday = None
        u.sex = None
        return u
    
    def get_link(self):
        return None

    @staticmethod
    def gen_name():
        return genericng.generate()

    def get_norm_country(self):
        return None

    def get_norm_location(self):
        return None

class GoogleUser(db.Model):
    # public
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    user = db.UserProperty()
    
    @staticmethod
    def auth(request, response):
        user = gusers.get_current_user()
        if user:
            u = GoogleUser.all().filter('user =', user).get()
            if not u:
                u = GoogleUser()
                u.user = user
                u.put()
            return u
        else:
            link = gusers.create_login_url("/chrome.html")
            response.redirect(link)
            return 'internal_work'
    
    def nickname(self):
        return self.user.nickname()

    def get_link(self):
        return None

    def get_norm_country(self):
        return None

    def get_norm_location(self):
        return None

class TestUser(db.Model):
    # public
    nickname = db.StringProperty()
    birthday = datetime.date.today()
    created = datetime.date.today()
    
    @staticmethod
    def auth(request, response):
        name = request.get('name')
        if name:
            query = db.GqlQuery("SELECT * FROM TestUser WHERE nickname=:name", name=name)
        else:
            query = TestUser.all()
        tu = query.get()
        if not tu:
            if not name:
                name="TestUser"
            tu = TestUser()
            tu.nickname = name
            tu.put()
        tu.access_friends = True
        return tu
    
    def get_link(self):
        return 'http://test.ru/user?=' + str(self.key())
    
    def get_norm_country(self):
        return None

    def get_norm_location(self):
        return None

class User(db.Model):
    auth_user = db.ReferenceProperty()
    nick = db.StringProperty()
    last_ip = db.StringProperty()
    country = db.StringProperty()
    location = db.StringProperty()

    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    last_visit = db.DateTimeProperty(auto_now_add=True)

    @staticmethod
    def auth(user_type, request, response):
        auth_user = user_type.auth(request, response)
        if auth_user == 'internal_work':
            return 'internal_work'
        query = db.GqlQuery("SELECT * FROM User WHERE auth_user=:user", user=auth_user)
        user = query.get()
        if user == None:
            # new one
            user = User.child_type()
            user.last_ip = request.remote_addr
            user.auth_user = auth_user
            user.country = auth_user.get_norm_country()
            user.location = auth_user.get_norm_location()
            user.put()
        else:
            # existed
            user.last_ip = request.remote_addr
            if callable(auth_user.nickname):
                nick = auth_user.nickname()
            else:
                nick = auth_user.nickname
            if user.nick != nick:
                user.nick = nick
            user.country = auth_user.get_norm_country()
            user.location = auth_user.get_norm_location()
            user.last_visit = datetime.datetime.now()
            user.put()
            user.auth_user = auth_user
        return user
    
    def nickname(self):
        if callable(self.auth_user.nickname):
            return self.auth_user.nickname()
        else:
            return self.auth_user.nickname

    def access_friends(self):
        return self.auth_user.access_friends
    
    def link(self):
        return self.auth_user.get_link()

    def sex(self):
        return getattr(self.auth_user, 'sex', None)

    def age(self):
        bd = getattr(self.auth_user, 'birthday', None)
        if bd:
            today = datetime.date.today()
            try: # raised when birth date is February 29 and the current year is not a leap year
                birthday = bd.replace(year=today.year)
            except ValueError:
                birthday = bd.replace(year=today.year, day=bd.day-1)
            if birthday > today:
                return today.year - bd.year - 1
            else:
                return today.year - bd.year


    def photo(self):
        if getattr(self.auth_user, 'photo', None):
            if callable(self.auth_user.photo):
                return self.auth_user.photo()
            else:
                return self.auth_user.photo
        return '/images/avatar_male.png'

    def auth_type(self):
        if isinstance(self.auth_user, VKUser):
            return 'vk'
        elif isinstance(self.auth_user, MMUser):
            return 'mm'
        elif isinstance(self.auth_user, FBUser):
            return 'fb'
        elif isinstance(self.auth_user, GuestUser):
            return 'guest'

