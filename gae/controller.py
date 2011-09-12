#-*-coding: utf-8 -*-
import google.appengine.ext.db
import djangosetup
from google.appengine.ext import webapp,db
from google.appengine.ext.webapp.util import run_wsgi_app, login_required
import logging
from django.utils import simplejson as json
import datetime
from google.appengine.ext.webapp import template
from google.appengine.ext import deferred
import os
import etc
import libs.gsfoid.utils
import model
from libs.gsfoid import utils, userlib
import base64
from libs import gaejson

utils.RequestHandlerExt.detect_lang_func = etc.detect_language

class TestPage(utils.RequestHandlerExt):
    def get(self):
        user = model.User.auth(userlib.TestUser, self.request, self)
        if user:
            session = model.Session.gen_session(user)
            utils.Cookie.set('gssession', str(session))

            vars = {
                'auth_type': 'test',
                'user': user,
                'session': session,
                'your_key': user.key(),
                'access_friends': user.access_friends(),
                'key': etc.map_key(),
                'server': etc.server(),
                'gserver': etc.gserver(),
                'settings': user.getSettingsAsArray()
            }
            if not user.tutorial_done:
                vars['run_tutorial'] = True

            self.renderPage('index.html', vars)
        else:
            self.renderText('Incorrect authorization')

###############################################################################

class VKPage(utils.RequestHandlerExt):
    def get(self):
        user = model.User.auth(userlib.VKUser, self.request, self)
        if user:
            session = model.Session.gen_session(user)
            utils.Cookie.set('gssession', str(session))

            vars = {
                'auth_type': 'vk',
                'user': user,
                'session': session,
                'your_key': user.key(),
                'access_friends': user.access_friends(),
                'key': etc.map_key(),
                'server': etc.server(),
                'gserver': etc.gserver(),
                'vk_app_id': userlib.VKUser.APP_ID,
                'settings': user.getSettingsAsArray()
            }
            if not user.tutorial_done:
                vars['run_tutorial'] = True

            self.renderPage('index.html', vars)
        else:
            self.renderText('Incorrect authorization')

class FriendsPage(utils.RequestHandlerExt):
    def post(self):
        user_type = self.request.get('type')
        ids = self.request.get('ids')
        ids = ids.split(',')
        def map_to_int(ids):
            tmp = []
            for i in ids:
                try:
                    i = int(i)
                    tmp.append(i)
                except ValueError:
                    continue
            return tmp
        if (not user_type) or (user_type=='vk'):
            user_table = 'VKUser'
            user_field = 'viewer_id'
            ids = map_to_int(ids)
        elif user_type=='fb':
            user_table = 'FBUser'
            user_field = 'user_id'
            ids = map_to_int(ids)
        else:
            user_table = 'MMUser'
            user_field = 'user_id'

        if ids==[]:
            self.renderJson({})
            return

        q = db.GqlQuery('SELECT * FROM ' + user_table + ' WHERE ' + user_field + ' IN :1', ids)
        vkusers = q.fetch(20)
        tmp = []
        for vku in vkusers:
            tmp.append(vku.key())
        q = db.GqlQuery('SELECT * FROM User WHERE auth_user IN :1', tmp)
        users = q.fetch(len(tmp))
        result = []
        for u in users:
            result.append(u.asArray())
        self.renderJson(result)

###############################################################################

# Moi Mir
class MMPage(utils.RequestHandlerExt):
    def get(self):
        try:
            user = model.User.auth(userlib.MMUser, self.request, self)
        except userlib.MMNotInstalledException:
            self.renderPage('mm_install.html')
        else:
            if user:
                session = model.Session.gen_session(user)
                utils.Cookie.set('gssession', str(session))

                vars = {
                    'auth_type': 'mm',
                    'user': user,
                    'session': session,
                    'your_key': user.key(),
                    'access_friends': user.access_friends(),
                    'key': etc.map_key(),
                    'server': etc.server(),
                    'gserver': etc.gserver(),
                    'settings': user.getSettingsAsArray(),
                    'mm_app_id': userlib.MMUser.MM_APP_ID,
                    'mm_private_key': userlib.MMUser.MM_PRIVATE_KEY
                }
                if not user.tutorial_done:
                    vars['run_tutorial'] = True

                self.renderPage('index.html', vars)
            else:
                self.renderText('Incorrect authorization')

###############################################################################

# odnoklassniki
class OdnkPage(utils.RequestHandlerExt):
    def get(self):
        user = model.User.auth(userlib.OdnkUser, self.request, self)
        if user:
            session = model.Session.gen_session(user)
            utils.Cookie.set('gssession', str(session))

            vars = {
                'auth_type': 'odnk',
                'user': user,
                'session': session,
                'your_key': user.key(),
                'access_friends': user.access_friends(),
                'key': etc.map_key(),
                'server': etc.server(),
                'gserver': etc.gserver(),
                'odnk_api_server': user.auth_user.api_server,
                'odnk_apiconnection': user.auth_user.apiconnection,
                'settings': user.getSettingsAsArray()
            }
            if not user.tutorial_done:
                vars['run_tutorial'] = True

            self.renderPage('index.html', vars)
        else:
            self.renderText('Incorrect authorization')

###############################################################################

class FBPage(utils.RequestHandlerExt):
    def post(self):
        user = model.User.auth(userlib.FBUser, self.request, self)

        if user == 'internal_work':
            return
        elif user:
            session = model.Session.gen_session(user)
            utils.Cookie.set('gssession', str(session))

            vars = {
                'auth_type': 'fb',
                'user': user,
                'session': session,
                'your_key': user.key(),
                'access_friends': user.access_friends(),
                'key': etc.map_key(),
                'server': etc.server(),
                'gserver': etc.gserver(),
                'settings': user.getSettingsAsArray(),
                'fb_app_id': userlib.FBUser.APP_ID,
                'access_token': user.auth_user.access_token,
            }
            if not user.tutorial_done:
                vars['run_tutorial'] = True

            self.renderPage('index.html', vars)
        else:
            self.renderText('Incorrect authorization')

###############################################################################

class GuestPage(utils.RequestHandlerExt):
    def get(self):
        user = model.User.auth(userlib.GuestUser, self.request, self)

        if user:
            session = model.Session.gen_session(user)
            utils.Cookie.set('gssession', str(session))

            vars = {
                'auth_type': 'guest',
                'user': user,
                'session': session,
                'your_key': user.key(),
                'access_friends': user.access_friends(),
                'key': etc.map_key(),
                'server': etc.server(),
                'gserver': etc.gserver(),
                'settings': user.getSettingsAsArray(),
                'hide_bottom': True,
            }
            if not user.tutorial_done:
                vars['run_tutorial'] = True

            self.renderPage('index.html', vars)
        else:
            self.renderText('Please reload the page in few seconds.')

###############################################################################

class GooglePage(utils.RequestHandlerExt):
    def get(self):
        user = model.User.auth(userlib.GoogleUser, self.request, self)

        if user == 'internal_work':
            return

        if user:
            session = model.Session.gen_session(user)
            utils.Cookie.set('gssession', str(session))

            vars = {
                'auth_type': 'google',
                'user': user,
                'session': session,
                'your_key': user.key(),
                'access_friends': False,
                'key': etc.map_key(),
                'server': etc.server(),
                'gserver': etc.gserver(),
                'settings': user.getSettingsAsArray(),
                'hide_bottom': True,
            }
            if not user.tutorial_done:
                vars['run_tutorial'] = True

            self.renderPage('index.html', vars)
        else:
            self.renderText('Please reload the page in few seconds.')

###############################################################################
class AuthPage(utils.RequestHandlerExt):
    def get(self):
        session = self.request.get('session')
        if session:
            user = model.Session.get_user_by_session(session)
            if user:
                self.renderJson({
                    'result': 'OK',
                    'key': str(user.key()),
                    'id': str(user.key().id()),
                    'name': user.nickname(),
                    'photo': user.photo(),
                    'score': user.score,
                    'link': user.getIntLink(),
                    'auth_type': user.auth_type(),
                    'country': user.country,
                    'location': user.location,
                    'place': 384,
                })
            else:
                self.renderJson({'result': 'wrong session'})
        else:
            self.renderJson('no session')

class SettingsJsonPage(utils.RequestHandlerExt):
    def get(self):
        session = self.request.get('session')
        if not session:
            session = utils.Cookie.get('gssession')
        if session:
            user = model.Session.get_user_by_session(session)
            if user:
                if self.request.get('sound'):
                    user.sSound = int(self.request.get('sound'))
                if self.request.get('soundLevel'):
                    val = int(self.request.get('soundLevel'))
                    if val>100:
                        val = 100
                    elif val<0:
                        val = 0
                    user.sSoundLevel = val
                if self.request.get('soundStart'):
                    user.sSoundStart = self.request.get('soundStart')=='1'
                if self.request.get('soundYourTurn'):
                    user.sSoundYourTurn = self.request.get('soundYourTurn')=='1'
                if self.request.get('soundAttack'):
                    user.sSoundAttack = self.request.get('soundAttack')=='1'
                if self.request.get('soundComing'):
                    user.sSoundComing = self.request.get('soundComing')=='1'

                tut = self.request.get('tutorialdone')
                if tut:
                    user.tutorial_done = int(tut)

                user.put()
                self.renderJson('ok')
            else:
                self.renderJson({'result': 'wrong session'})
        else:
            self.renderJson('no session')

class MapEditorPage(utils.RequestHandlerExt):
    def get(self):
        self.renderPage('mapeditor.html', {
            'key': etc.map_key()
        })

class HomePage(utils.RequestHandlerExt):
    def get(self):
        userlib.VKUser.setup()
        self.renderPage('home.html', {
            'vk_app_id': userlib.VKUser.APP_ID
        })

class LeadersPage(utils.RequestHandlerExt):
    def get(self):
        vars = {}
        vars['cur_season'] = model.StatSeason.getCurrentSeasonName()
        vars['top'] = model.User.all().order('-score').fetch(25)
        vars['top_today'] = model.User.all().order('-stat_score_today').fetch(25)
        vars['top_ppg'] = model.User.all().order('-stat_ppg_top').fetch(25)
        vars['top_total'] = model.User.all().order('-score_total').fetch(25)
        vars['prev_season'] = model.StatSeason.getSeasonNameById(model.StatSeason.getCurrentSeason() -1)
        vars['prev_season_link'] = '/leaders/%s.html' % (model.StatSeason.getCurrentSeason() -1)
        self.renderPage('leaders.html', vars)

class LeadersOldPage(utils.RequestHandlerExt):
    def get(self, season):
        vars = {}
        season = int(season)
        q = model.StatSeason.all().filter('season =', season)
        s = q.get()
        if not s:
            self.error(404)
            return
        vars['season_name'] = s.getSeasonName()
        vars['next_season'] = model.StatSeason.getSeasonNameById(season +1)
        if season>1:
            vars['prev_season'] = model.StatSeason.getSeasonNameById(season -1)
            vars['prev_season_link'] = '/leaders/%s.html' % (season-1)
        if model.StatSeason.getCurrentSeason() <= season+1:
            vars['next_season_link'] = '/leaders.html'
        else:
            vars['next_season_link'] = '/leaders/%s.html' % (season+1)
        q = model.StatSeason.all().filter('season =', season)
        vars['top'] = q.order('-score').fetch(25)
        q = model.StatSeason.all().filter('season =', season)
        vars['top_ppg'] = q.order('-stat_ppg_top').fetch(25)
        self.renderPage('leaders_old.html', vars)

class AdminPage(utils.RequestHandlerExt):
    def post(self):
        # damn this method's code!
        back_url = self.request.headers['Referer']
        if not back_url:
            self.renderText('Error occured')
            return
        session = self.request.get('session')
        if not session:
            session = utils.Cookie.get('gssession')
        if not session:
            self.renderText('Error occured')
            return

        admin = model.Session.get_user_by_session(session)
        if admin and admin.admin_rights:
            # penalties
            if self.request.get('action') == 'penalty':
                prev_penalty_id = self.request.get('penalty_id')
                user_id = self.request.get('user_id')
                if not user_id:
                    self.renderText('User ID should be set')
                    return
                user = model.User.get_by_id(int(user_id))
                if not user:
                    self.renderText('User not found')
                    return
                if user.admin_rights and admin.admin_rights != model.User.ADMIN_RIGHT_ALL:
                    self.renderText('You cannot fine this moderator')
                    return
            
                period = self.request.get('period')
                if period:
                    period = int(period)
                    if period < 0:
                        self.renderText('Incorrect period value')
                        return

                message = self.request.get('message')
                if not message or len(message)<5:
                    self.renderText("You've gotta write a comment")
                    return

                game_id = self.request.get('game_id')
                if game_id:
                    game_id = int(game_id)
                    if game_id<1:
                        self.renderText('Wrong game id')
                        return
                else:
                    game_id = None

                score = self.request.get('score')
                if score:
                    score = int(score)
                    if score == 0:
                        score = None
                    elif score < 0:
                        self.renderText('Incorrect score penalty value')
                        return

                    if admin.admin_rights!=1:
                        if not (admin.getAdminRight(model.User.ADMIN_RIGHT_SCORE) or admin.getAdminRight(model.User.ADMIN_RIGHT_SCORE_J)):
                            self.renderText('No access for score penalty')
                            return
                        elif admin.getAdminRight(model.User.ADMIN_RIGHT_SCORE_J) and (score > 300):
                            self.renderText('You cannot fine more than 300 score points')
                            return
                
                logging.info(admin.admin_rights)
                user_with = None
                if self.request.get('user_with'):
                    user_with_id = int(self.request.get('user_with'))
                    user_with = model.User.get_by_id(user_with_id)
                    if not user_with:
                        self.renderText('Incorrect user_id=' % user_with_id)
                        return
                    if admin.admin_rights!=1:
                        if not (admin.getAdminRight(model.User.ADMIN_RIGHT_BAN_PLAY_TOGETHER) or admin.getAdminRight(model.User.ADMIN_RIGHT_BAN_PLAY_TOGETHER_J)):
                            self.renderText('No access for banning to play together')
                            return
                        elif admin.getAdminRight(model.User.ADMIN_RIGHT_BAN_PLAY_TOGETHER_J) and (period > 10080): # 7 days
                            self.renderText('You cannot fine more than for 7 days period')
                            return
                    if period < 1:
                        self.renderText('Please specify the period for the ban')
                        return

                chat_ban = False
                if self.request.get('chat_ban'):
                    chat_ban = True
                    if admin.admin_rights!=1:
                        if not (admin.getAdminRight(model.User.ADMIN_RIGHT_BAN_CHAT) or admin.getAdminRight(model.User.ADMIN_RIGHT_BAN_CHAT_J)):
                            self.renderText('No access to ban chat')
                            return
                        elif admin.getAdminRight(model.User.ADMIN_RIGHT_BAN_CHAT_J) and (period > 10080): # 7 days
                            self.renderText('You cannot fine more than for 7 days period')
                            return
                    if period < 1:
                        self.renderText('Please specify the period for the chat ban')
                        return
                
                total_ban = False
                if self.request.get('total_ban'):
                    total_ban = True
                    if not admin.getAdminRight(model.User.ADMIN_RIGHT_BAN_TOTAL):
                        self.renderText('No access for banning chat')
                        return

                if not (total_ban or chat_ban or user_with or score):
                    self.renderText('No ban set')
                    return
                
                user.add_penalty(admin, period, message, score, user_with, chat_ban, total_ban, game_id, prev_penalty_id)
                self.redirect(back_url)
                return

    def get(self):
        session = self.request.get('session')
        if not session:
            session = utils.Cookie.get('gssession')
        if not session:
            self.renderText('Error occured')
            return

        admin = model.Session.get_user_by_session(session)
        if self.DEV_SERVER:
            admin.admin_rights=1;
            admin.put()
        if admin and admin.admin_rights:
            vars = {}
            # search user
            if self.request.get('search_user'):
                vars['users_found'] = []
                search_name = self.request.get('search_name')
                if search_name:
                    vars['search_name'] = search_name
                    u = model.User.all().filter('nick =', search_name).get()
                    if u:
                        vars['users_found'].append(u)
                search_vk = self.request.get('search_vk_id')
                if search_vk:
                    vars['search_vk_id'] = search_vk
                    v = userlib.VKUser.all().filter('viewer_id =', int(search_vk)).get()
                    if v:
                        u = model.User.all().filter('auth_user =', v).get()
                        if u:
                            vars['users_found'].append(u)
                self.renderPage('admin.html', vars)

            # penalies log
            elif self.request.get('action') == 'log':
                vars['penalies'] = model.Penalty.all().order('-created').fetch(100)
                self.renderPage('admin_log.html', vars)

            # last games
            elif self.request.get('action') == 'last_games':
                only_games = []
                user_id = self.request.get('user_id')
                if user_id:
                    u = model.User.get_by_id(int(user_id))
                    stats = model.Stat.all().filter('user', u).order('-created').fetch(20)
                    only_games = []
                    for s in stats:
                        only_games.append(s.game)
                    vars['user'] = u
                q = model.GameReplay.all()
                if only_games:
                    q.filter('game IN', only_games)
                if self.request.get('only') == 'abuse':
                    q.filter('abuse ==', True)
                vars['games'] = q.order('-created').fetch(100)
                self.renderPage('admin_last_games.html', vars)

            # home admin page
            else:
                self.renderPage('admin.html', vars)
        else:
            self.renderText('Error occured')
            return

class PenaltiesPage(utils.RequestHandlerExt):
    def get(self):
        q = model.Penalty.all().filter('applied =', True).filter('on_twisted =', True);
        resp = []
        for p in q.fetch(q.count()):
            if p.expired<=datetime.datetime.now():
                p.applied = False
                p.put()
            else:
                resp.append(p.asArray())
        self.renderJson(resp)

class TutorialPage(utils.RequestHandlerExt):
    def get(self, lang):
        session = self.request.get('session')
        # get user
        user = None
        if session:
            user = model.Session.get_user_by_session(session)
        if not user:
            self.error(403)
            return
        f = open('tutorial.map', 'r')
        tmp = f.read()
        # replaces
        tmp = tmp.replace('{your_name}', user.nickname().encode('utf8'))
        link = ''
        if user.link():
            link = user.link().encode('utf8')
        tmp = tmp.replace('{your_link}', link)
        tmp = tmp.replace('{your_key}', str(user.key()))
        tmp = tmp.replace('{your_photo}', user.photo().encode('utf8'))
        # allright render it
        f.close()
        self.renderText(tmp)

class HelpPage(utils.RequestHandlerExt):
    def get(self):
        vars = {
            'type': self.request.get('type')
        }
        tpl = 'help.html'
        if self.lang=='en':
            tpl = 'help_en.html'
        self.renderPage(tpl, vars)

class UserProfilePage(utils.RequestHandlerExt):
    def get(self, id):
        id = int(id)
        user = model.User.get_by_id(id)
        if not user:
            self.error(404)
            return
        def getPlaces(obj):
            places = {
                4: [0,0,0,0],
                6: [0,0,0,0,0,0],
                8: [0,0,0,0,0,0,0,0]
            }
            if user.stat_games>0:
                places = {
                    4: [
                        int(float(user.stat_place1)/user.stat_games *100),
                        int(float(user.stat_place2)/user.stat_games *100),
                        int(float(user.stat_place3)/user.stat_games *100),
                        int(float(user.stat_place4)/user.stat_games *100)],
                    6: [
                        int(float(user.stat_6_place1)/user.stat_games *100),
                        int(float(user.stat_6_place2)/user.stat_games *100),
                        int(float(user.stat_6_place3)/user.stat_games *100),
                        int(float(user.stat_6_place4)/user.stat_games *100),
                        int(float(user.stat_6_place5)/user.stat_games *100),
                        int(float(user.stat_6_place6)/user.stat_games *100)],
                    8: [
                        int(float(user.stat_8_place1)/user.stat_games *100),
                        int(float(user.stat_8_place2)/user.stat_games *100),
                        int(float(user.stat_8_place3)/user.stat_games *100),
                        int(float(user.stat_8_place4)/user.stat_games *100),
                        int(float(user.stat_8_place5)/user.stat_games *100),
                        int(float(user.stat_8_place6)/user.stat_games *100),
                        int(float(user.stat_8_place7)/user.stat_games *100),
                        int(float(user.stat_8_place8)/user.stat_games *100)],
                }
            return places
        
        limit=10
        q = model.Stat.getLastGamesQuery(user)
        games = q.fetch(limit)
        cursor = q.cursor()
        q.with_cursor(cursor)
        if q.count(1)==0:
            cursor = None

        stat_season = model.StatSeason.all().filter('user =', user).order('-season').fetch(12) # temporary for 6 month
        is_reward = False
        for s in stat_season:
            if s.isRewarded():
                is_reward = True

        vars = {'user': user, 
                'places': getPlaces(user),
                'games': games, 'games_empty': len(games)==0,
                'user_type': user.auth_type(),
                'cur_season': model.StatSeason.getCurrentSeasonName(),
                'is_reward': is_reward,
                'is_stat_season': len(stat_season)>0,
                'stat_season': stat_season,
                'gserver': etc.gserver(),
                'cursor': cursor
        }

        if user.has_penalties:
            # load penalties
            q = db.GqlQuery('SELECT * FROM Penalty WHERE user=:1 ORDER BY created DESC', user)
            vars['penalties'] = q.fetch(5)

        session = self.request.get('session')
        if not session:
            session = utils.Cookie.get('gssession')
            if session:
                me = model.Session.get_user_by_session(session)
                if me:
                    vars['me'] = me

        self.renderPage('user.html', vars)

# game replays and ratings

import zlib
class GameReplayPage(utils.RequestHandlerExt):
    def get(self, id):
        try:
            s = int(id)
            r = model.GameReplay.get_by_id(s)
        except ValueError:
            r = model.GameReplay.all().filter('game =', id).get()
            if r:
                self.redirect('/replay/%s' % r.key().id())
                return
        if not r:
            self.error(404)
            return
        if not r:
            self.error(404)
            return
        vars = {
            'server': etc.server(),
            'gserver': etc.gserver(),
        }
        vars['key'] = etc.map_key()
        vars['replay'] = r
        if self.request.query_string == 'chat_only':
            vars['record'] = zlib.decompress(r.replay)
            self.renderPage('replay_chat.html', vars)
        else:
            vars['record'] = zlib.decompress(r.replay).replace('\"', '\\"')
            self.renderPage('index.html', vars)

class ScorePage(utils.RequestHandlerExt):
    def get(self):
        if self.request.get('action')=='add' and self.request.get('pwd')==etc.TWISTED_PWD_IN:
            key = self.request.get('key')
            score = self.request.get('score')
            place = self.request.get('place')
            map = self.request.get('map')
            turn = self.request.get('turn')
            game = self.request.get('game')
            turn_order = self.request.get('turn_order')

            kills = self.request.get('kills')
            attacks = self.request.get('attacks')
            defends = self.request.get('defends')
            domination = self.request.get('domination')
            luck = self.request.get('luck')

            players = self.request.get('players')
            if not players:
                players = 4
            user = model.User.all().filter('__key__', db.Key(key)).get()
            if user:
                user.add_score(map,place,score,turn,game,players,kills,attacks,defends,domination,luck,turn_order)
                self.renderText('OK')
            else:
                self.renderText('User Not Found')
        else:
            self.renderText('trololo')

class TopPage(utils.RequestHandlerExt):
    def get(self):
        self.renderText(model.User.get_top_json())

class LastGamesJsonPage(utils.RequestHandlerExt):
    def get(self):
        id = self.request.get('user_id')
        id = int(id)
        user = model.User.get_by_id(id)
        if not user:
            self.error(404)
            return
        q = model.Stat.getLastGamesQuery(user)
        cursor = self.request.get('cursor')
        if cursor:
            q.with_cursor(cursor)
        limit = 10
        games = q.fetch(limit)
        cursor = q.cursor()
        q.with_cursor(cursor)
        if q.count(1)==0:
            cursor = None
        vars = {}
        if cursor:
            vars = {'cursor': cursor}
        vars['add'] = self.getRenderPage('user_stats.html', {'games': games})
        self.renderJson(vars)

class UploadGamePage(utils.RequestHandlerExt):
    def post(self):
        if self.request.get('pwd')==etc.TWISTED_PWD_IN:
            game = self.request.get('game')
            _map = self.request.get('map')
            players = self.request.get('players')
            replay = self.request.POST.get('replay')
            abuse = self.request.POST.get('abuse')
            if not (game and map and players and replay):
                self.error(404)
                return
            r = model.GameReplay()
            r.game = game
            r.map = _map
            r.players = int(players)
            r.replay = str(base64.b64decode(replay))
            if abuse == '1':
                r.abuse = True
            r.put()

            # link to stats
            deferred.defer(r.link_stats, game, players)

            self.renderText('OK')
            return
        self.error(403)

# data sync
class DownloadJsonPage(utils.RequestHandlerExt):
    def get(self):
        if self.request.get('pass') != etc.SYNC_PASS:
            self.renderText('access denied')
            return
        models = ['model.User', 'model.Stat', 'userlib.VKUser',
            'userlib.FBUser', 'userlib.MMUser', 'userlib.GuestUser',
            'userlib.GoogleUser'
            ]
        kind = self.request.get('kind')
        if not kind in models:
            self.renderText('kind not found')
            return
        limit = 300
        if self.request.get('limit'):
            limit = int(self.request.get('limit'))
        q = eval(kind).all()
        if self.request.get('filter'):
            val = eval(self.request.get('value'))
            q.filter(self.request.get('filter'), val)
        if self.request.get('cursor'):
            q.with_cursor(self.request.get('cursor'))
        data = q.fetch(limit)
        cursor = q.cursor()
        q.with_cursor(cursor)
        if q.count(1)==0:
            cursor = None
        js = gaejson.encode([cursor, data])
        self.renderText(js)

application = webapp.WSGIApplication(
        [
            # game frames
            ('/facebook.html', FBPage),
            ('/vkontakte.html', VKPage),
            ('/moimir.html', MMPage),
            ('/odnk.html', OdnkPage),
            ('/chrome.html', GooglePage),
            ('/guest.html', GuestPage),
            ('/test.html', TestPage),

            ('/admin.html', AdminPage),

            # site pages
            ('/leaders.html', LeadersPage),
            ('/leaders/(\d+).html', LeadersOldPage),
            (r'/user/([0-9]+)', UserProfilePage),
            (r'/replay/(.+)', GameReplayPage),
            ('/map-editor.html', MapEditorPage),
            ('/help.html', HelpPage),
            
            # twisted communication
            ('/auth', AuthPage),
            ('/penalties', PenaltiesPage),
            ('/rating/upload_game', UploadGamePage),
            ('/rating/score.html', ScorePage),

            # ajax
            ('/settings.json', SettingsJsonPage),
            (r'/tutorial/(.+)\.json', TutorialPage),
            ('/vkontakte/friends.html', FriendsPage),
            ('/rating/top.json', TopPage),
            ('/rating/last-games.json', LastGamesJsonPage),

            # data sync
            ('/data/download.json', DownloadJsonPage),
            
            # home page and everything
            (r'/.*', HomePage),
        ],
        debug=True)

def main():
    template.register_template_library('filters.mytfilters')
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
