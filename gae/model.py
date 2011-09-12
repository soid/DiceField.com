#-*-coding: utf-8 -*-
from google.appengine.ext import db
from libs.gsfoid import userlib

import random
import hashlib
import time
import logging
import datetime
from google.appengine.api import memcache
from django.utils import simplejson as json
from google.appengine.ext import deferred
import etc
import urllib, urllib2
import math
from libs.gsfoid import utils
import etc

from django.utils.translation import ugettext as _


class User(userlib.User):
    TOP_JSON = 'User.TOP_JSON'

    title = db.StringProperty()

    # stat for all time
    score_total = db.IntegerProperty(default=0)
    stat_games_total = db.IntegerProperty(default=0)

    # current season stat
    score = db.IntegerProperty(default=0)
    stat_ppg = db.FloatProperty(default=0.0) # points per game
    stat_ppg_top = db.FloatProperty(default=0.0) # ppg for games>15

    stat_games = db.IntegerProperty(default=0)
    stat_games4 = db.IntegerProperty(default=0) # 4 players
    stat_games6 = db.IntegerProperty(default=0) # 6 players
    stat_games8 = db.IntegerProperty(default=0) # 8 players

    stat_kills = db.IntegerProperty(default=0)

    stat_luck = db.FloatProperty(default=0.0) # average for games>15
    stat_luck_sum = db.FloatProperty(default=0.0)
    stat_domination = db.FloatProperty(default=0.0) # average for games>15
    stat_domination_sum = db.FloatProperty(default=0.0)

    stat_attacks = db.IntegerProperty(default=0)
    stat_defends = db.IntegerProperty(default=0)
    stat_attdef_top = db.FloatProperty(default=0.0) # attacks / deffenders for games>15
    stat_defatt_top = db.FloatProperty(default=0.0) # attacks / deffenders for games>15
    
    # today stat
    stat_score_today = db.IntegerProperty(default=0)

    # 4 players map
    stat_place1 = db.IntegerProperty(default=0)
    stat_place2 = db.IntegerProperty(default=0)
    stat_place3 = db.IntegerProperty(default=0)
    stat_place4 = db.IntegerProperty(default=0)

    # 6 players map
    stat_6_place1 = db.IntegerProperty(default=0)
    stat_6_place2 = db.IntegerProperty(default=0)
    stat_6_place3 = db.IntegerProperty(default=0)
    stat_6_place4 = db.IntegerProperty(default=0)
    stat_6_place5 = db.IntegerProperty(default=0)
    stat_6_place6 = db.IntegerProperty(default=0)

    # 8 players map
    stat_8_place1 = db.IntegerProperty(default=0)
    stat_8_place2 = db.IntegerProperty(default=0)
    stat_8_place3 = db.IntegerProperty(default=0)
    stat_8_place4 = db.IntegerProperty(default=0)
    stat_8_place5 = db.IntegerProperty(default=0)
    stat_8_place6 = db.IntegerProperty(default=0)
    stat_8_place7 = db.IntegerProperty(default=0)
    stat_8_place8 = db.IntegerProperty(default=0)

    # user's settings
    sSound = db.IntegerProperty(default=1)
    sSoundLevel = db.IntegerProperty(default=100)
    sSoundStart = db.BooleanProperty(default=True)
    sSoundYourTurn = db.BooleanProperty(default=True)
    sSoundAttack = db.BooleanProperty(default=True)
    sSoundComing = db.BooleanProperty(default=True)

    # other
    admin_rights = db.IntegerProperty(default=None)
    has_penalties = db.BooleanProperty()
    tutorial_done = db.IntegerProperty(default=10)

    # boosts
    boost_score = db.IntegerProperty(default=None)
    boost_date = db.DateTimeProperty()

    @staticmethod
    def get_top(limit=10):
        q = User.all()
        q.order("-score")
        return q.fetch(limit)
        
    @staticmethod
    def get_top_json(limit=10):
        mem = memcache.get(User.TOP_JSON)
        if mem is None:
            top = map(lambda e: e.asArray(), User.get_top())
            j = json.dumps(top)
            memcache.set(User.TOP_JSON, j)
            return j
        else:
            return mem

    @staticmethod
    def give_boosts(users, boost_score=100):
        vkusers = []
        mmusers = []
        vkid2u = {}
        mmid2u = {}
        for u in users:
            if type(u.auth_user) in [userlib.VKUser, userlib.MMUser]:
                if type(u.auth_user)==userlib.VKUser:
                    vkusers.append(u.auth_user)
                    vkid2u[str(u.auth_user.viewer_id)] = u
                elif type(u.auth_user)==userlib.MMUser:
                    mmusers.append(u.auth_user)
                    mmid2u[str(u.auth_user.user_id)] = u
        # send notification
        result = {}
        if len(vkusers)>0:
            r = result['vk'] = userlib.VKUser.send_notifications(vkusers,
                u'Воины Кубиков соскучились по тебе! Зайди в игру, сыграй партию и получи %s очков бонуса.' % boost_score)
            for id in r[1]:
                u = vkid2u[id]
                u.boost_score = boost_score
                u.boost_date = datetime.datetime.now()
                u.put()
        if len(mmusers)>0:
            r = result['mm'] = userlib.MMUser.send_notifications(mmusers,
                'Воины Кубиков соскучились по тебе! Сыграй партию и получи %s очков бонуса.' % boost_score)
            for id in r[1]:
                u = mmid2u[id]
                u.boost_score = boost_score
                u.boost_date = datetime.datetime.now()
                u.put()
        return result

    def add_penalty(self, admin, period, message, score=None, user_with=None, chat_ban=None,
            total_ban=None, game_id=None, edit_id=None, both=True):
        if edit_id:
            edit_id = int(edit_id)
            p = Penalty.get_by_id(edit_id)
            if not p:
                raise Exception('Penalty does not exist')
            prev_score = p.penalty_score
            if p.isExpired():
                raise Exception('Cannot edit expired panalty')
        else:
            p = Penalty()
        p.admin = admin
        p.user = self
        p.message = message
        p.applied = True
        if score:
            p.penalty_score = score
        if user_with:
            p.penalty_playing_together = user_with
            p.on_twisted = True
        if chat_ban:
            p.ban_chat = True
            p.on_twisted = True
        if total_ban:
            p.total_ban = True
            p.on_twisted = True
        if period:
            if not p.created:
                now = datetime.datetime.now()
            else:
                now = p.created
            p.expired = now + datetime.timedelta(0, 0, 0, 0, int(period))
        if game_id:
            p.game_id = game_id
        p.put()
        if not edit_id:
            if score:
                self.add_score('Penalty', 0, -score, 0, '')
                p.on_twisted = True
        else:
            if score != prev_score:
                self.add_score('Penalty', 0, prev_score-score, 0, '')
                p.on_twisted = True
        self.has_penalties = True
        self.put()
        if p.on_twisted:
            params = {'penalty': json.dumps(p.asArray())}
            if edit_id:
                params['edit'] = '1'
                if score!=prev_score:
                    params['score'] = prev_score-score
            request_twisted_webdoor(params)

        if user_with and both and (not edit_id):
            # ban both
            user_with.add_penalty(admin, period, message, score, self, chat_ban, total_ban, game_id, edit_id=edit_id, both=False)

    def add_score(self,map,place,score,turn,game,players=4,kills=0,attacks=None,defends=None,domination=None,
                  luck=0.5,turn_order=None):
        place = int(place)
        score = int(score)
        turn = int(turn)
        players = int(players)
        old_score = self.score
        
        if not self.score:
            self.score = 0
        self.score += score
        self.stat_games += 1

        if kills:
            kills = int(kills)
            self.stat_kills += kills
        else:
            kills = None

        if turn_order:
            turn_order = int(turn_order)
        else:
            turn_order = None

        # attacks, defends
        if attacks:
            attacks = int(attacks)
            self.stat_attacks += attacks
        else:
            attacks = None
        if defends:
            defends = int(defends)
            self.stat_defends += defends
        else:
            defends = None

        setattr(self, "stat_games" + str(players),
            getattr(self, "stat_games" + str(players), 0) + 1);

        # domination and luck (agerage values)
        if domination:
            domination = float(domination)
            if not self.stat_domination_sum:
                self.stat_domination_sum = 0.0
            self.stat_domination_sum += domination
        else:
            attacks = None

        if luck:
            luck = float(luck)
            if not self.stat_luck_sum:
                self.stat_luck_sum = 0.0
            self.stat_luck_sum += luck
        else:
            luck = None

        # general stat
        self.stat_score_today += score
        self.score_total += score
        self.stat_games_total += 1

        m = ""
        if players != 4:
            m = str(players) + "_"
        setattr(self, "stat_" + m + "place" + str(place),
            getattr(self, "stat_" + m + "place" + str(place), 0) + 1);

        # save scores
        if self.score <0:
            self.stat_score_today -= self.score
            self.score_total -= self.score
            self.score = 0

        self.stat_ppg = float(self.score) / self.stat_games

        # calculus stats for more than 15 games
        if self.stat_games > 15:
            self.stat_ppg_top = self.stat_ppg
            if self.stat_defends>0:
                self.stat_attdef_top = float(self.stat_attacks) / self.stat_defends
            if self.stat_attacks>0:
                self.stat_defatt_top = float(self.stat_defends) / self.stat_attacks
            if (self.stat_attacks + self.stat_defends) > 0:
                self.stat_luck = self.stat_luck_sum / (self.stat_attacks + self.stat_defends)
            self.stat_domination = self.stat_domination_sum / self.stat_games

        # save score in UserStatPlace
        got_to_calc_places = False
        if old_score>0:
            usp = UserStatPlace.all().filter('score =', old_score).get()
            if usp:
                if usp.count <= 1:
                    usp.delete()
                else:
                    usp.count -= 1
                    usp.put()
                    got_to_calc_places = True

        if self.score > 0:
            usp = UserStatPlace.all().filter('score =', self.score).get()
            if usp:
                usp.count += 1
            else:
                usp = UserStatPlace()
                usp.score = self.score
                usp.count = 1
                usp.place = 0
                got_to_calc_places = True
            usp.put()

        # calc places
        if got_to_calc_places:
            deferred.defer(self.calc_places, old_score, self.score)

        # add boost
        if self.boost_score:
            deferred.defer(self.add_boost, self.key().id(), _countdown=3)

        # save stat
        deferred.defer(self.addStat, map, score, self.score, place, players, turn,
            turn_order, kills, luck, domination, attacks, defends, game)

        self.put()

    def addStat(self, map, score, total_score, place, players, turn,
            turn_order, kills, luck, domination, attacks, defends, game):
        s = Stat()
        s.user = self
        s.map = map
        s.score = score
        s.total_score = total_score
        s.place = place
        s.players = players
        s.turn = turn
        s.turn_order = turn_order
        s.kills = kills
        s.stat_luck = luck
        s.stat_domination = domination
        s.stat_attacks = attacks
        s.stat_defends = defends
        s.game = str(game)
        s.put()

        memcache.delete(User.TOP_JSON)

    def getSettingsAsArray(self):
        return {
            'soundOn': bool(self.sSound),
            'soundLevel': self.sSoundLevel,
            'soundStart': self.sSoundStart,
            'soundYourTurn': self.sSoundYourTurn,
            'soundAttack': self.sSoundAttack,
            'soundComing': self.sSoundComing,
        }

    def getPlaceRange(self):
        ups = UserStatPlace.all().filter('score =', self.score).get()
        if ups and ups.place>0:
            return [ups.place, ups.count -1]
        else:
            return [None, None]

    def getPlace(self):
        ups = UserStatPlace.all().filter('score =', self.score).get()
        if ups and ups.place>0:
            txt = str(ups.place)
            if ups.count>1:
                txt += '-' + str(ups.place + ups.count -1)
            return txt
        else:
            return None

    def ppg(self):
        return self.stat_ppg

    ADMIN_RIGHT_ALL = 1
    ADMIN_RIGHT_BAN_TOTAL = 2
    ADMIN_RIGHT_BAN_CHAT_J = 4 # J means junior
    ADMIN_RIGHT_BAN_CHAT = 8
    ADMIN_RIGHT_BAN_PLAY_TOGETHER_J = 16
    ADMIN_RIGHT_BAN_PLAY_TOGETHER = 32
    ADMIN_RIGHT_SCORE_J = 64
    ADMIN_RIGHT_SCORE = 128
    ADMIN_RIGHT_GRANT = 256

    def getAdminRight(self, right):
        if self.admin_rights==User.ADMIN_RIGHT_ALL:
            return True
        return (self.admin_rights & right) == right

    def getAdminRightBanTotal(self):
        return self.getAdminRight(User.ADMIN_RIGHT_BAN_TOTAL)

    def getAdminRightBanChat(self):
        return self.getAdminRight(User.ADMIN_RIGHT_BAN_CHAT) or self.getAdminRight(User.ADMIN_RIGHT_BAN_CHAT_J)

    def getAdminRightBanPlayTogether(self):
        return self.getAdminRight(User.ADMIN_RIGHT_BAN_PLAY_TOGETHER) or self.getAdminRight(User.ADMIN_RIGHT_BAN_PLAY_TOGETHER_J)

    def getAdminRightBanScore(self):
        return self.getAdminRight(User.ADMIN_RIGHT_SCORE) or self.getAdminRight(User.ADMIN_RIGHT_SCORE_J)

    def getIntLink(self):
        """
        Get internal social network link
        """
        return "/user/" + str(self.key().id())

    def nickFull(self):
        if self.auth_type()=='guest':
            return _(u'Гость ') + self.nickname()
        return self.nickname()

    def asArray(self):
        res = {
            'name': self.nickname(),
            'score': self.score,
            'link': self.getIntLink(),
            'photo': self.photo(),
            't': self.auth_type()
        }
        if type(self.auth_user)==userlib.GuestUser:
            res['t'] = self.auth_type()
        return res

    # deferred methods

    def add_boost(self, user_id):
        u = User.get_by_id(user_id)
        if u and u.boost_score:
            score = u.boost_score
            u.boost_score = None
            u.add_score('Bonus', 0, score, 0, '')
            deferred.defer(request_twisted_webdoor, {
                'action': 'edit_score',
                'user_id': user_id,
                'score': u.score
            }, True)
        else:
            logging.warning('add_boost: User not found %s' % user_id)

    def calc_places(self,old,new,cursor=None):
        q = UserStatPlace.all().filter('score >=', min(old,new)) \
            .filter('score <=', max(old,new)).order('-score')
        if cursor:
            q.with_cursor(cursor[0])
            mplace = cursor[1]
            mscore = cursor[2]
        else:
            muser = UserStatPlace.all().filter('score >', max(old,new)).order('score').get()
            if muser:
                mplace = muser.place
                mscore = muser.score
            else:
                mplace = 0
                mscore = 9999999999 # maximum scores
        
        # update users
        users = q.fetch(50)
        for u in users:
            if u.score == 0:
                break
            mplace += 1
            mscore = u.score
            if u.place != mplace:
                u.place = mplace
                u.put()
            mplace += u.count -1
        cursor = q.cursor() 
        q.with_cursor(cursor)
        if q.count(1) > 0:
            # there're more results
            deferred.defer(self.calc_places, old, new, [cursor, mplace, mscore])

    def reset_today_stat(self, cursor=None, greater=True):
        if greater:
            qu = db.GqlQuery('SELECT * FROM User WHERE stat_score_today > 0')
        else:
            qu = db.GqlQuery('SELECT * FROM User WHERE stat_score_today < 0')
        if cursor:
            qu.with_cursor(cursor)
        us = qu.fetch(100)
        for u in us:
            deferred.defer(u.reset_today_user_stat, u.key())
        cursor = qu.cursor() 
        qu.with_cursor(cursor)
        if qu.count(1) > 0:
            # there're more results
            deferred.defer(self.reset_today_stat, cursor, greater)
        elif greater:
            deferred.defer(self.reset_today_stat, None, False)
        return 0

    def reset_today_user_stat(self, key):
        user = User.get_by_id(key.id())
        user.stat_score_today = 0
        user.put()

    def new_season(self, cursor=None):
        q = db.GqlQuery('SELECT * FROM User WHERE stat_games > 0')
        if cursor:
            q.with_cursor(cursor)
        us = q.fetch(100)
        for u in us:
            # process user for a new season
            StatSeason.moveStat(u)
        cursor = q.cursor()
        q.with_cursor(cursor)
        if q.count(100) > 0:
            # there're more results
            deferred.defer(self.new_season, cursor)
        else:
            # all right, next step - remove all UserStatPlace
            self.clear_stat_places()

    def clear_stat_places(self, cursor=None):
        q = UserStatPlace.all()
        if cursor:
            q.with_cursor(cursor)
        for usp in q.fetch(300):
            usp.delete()
        cursor = q.cursor()
        q.with_cursor(cursor)
        if q.count(1) > 0:
            # there're more results
            deferred.defer(self.clear_stat_places, cursor)

userlib.User.child_type = User

class UserStatPlace(db.Model):
    """
    list of places according to scores
    """
    score = db.IntegerProperty()
    count = db.IntegerProperty(default=0)
    place = db.IntegerProperty(default=0)

class Stat(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)
    user = db.ReferenceProperty(collection_name='user_')
    score = db.IntegerProperty()
    total_score = db.IntegerProperty()
    map = db.StringProperty()
    place = db.IntegerProperty()
    players = db.IntegerProperty(default=4)
    turn = db.IntegerProperty()
    turn_order = db.IntegerProperty()
    game = db.StringProperty()
    rgame = db.ReferenceProperty(collection_name='rgame')

    kills = db.IntegerProperty(default=0)
    stat_luck = db.FloatProperty(default=0.0)
    stat_domination = db.FloatProperty(default=0.0)
    stat_attacks = db.IntegerProperty(default=0)
    stat_defends = db.IntegerProperty(default=0)

    @staticmethod
    def getLastGamesQuery(user):
        return db.GqlQuery('SELECT * FROM Stat WHERE user=:1 ORDER BY created DESC', user)

    @staticmethod
    def clearStatInTwisted():
        request_twisted_webdoor({'action': 'clear_stat'})

    def asArray(self):
        return {
            'created': self.created.strftime("%d.%m.%Y"),
            'map': self.map,
            'turn': self.turn,
            'place': self.place,
            'score': self.score,
            'total_score': self.total_score,
            'game': self.game
        }

class StatSeason(db.Model):
    user = db.ReferenceProperty()
    season = db.IntegerProperty()

    # stat
    score = db.IntegerProperty(default=0)
    stat_ppg = db.FloatProperty(default=0.0)
    stat_ppg_top = db.FloatProperty(default=0.0)
    place = db.IntegerProperty()
    place_range = db.IntegerProperty()
    stat_games = db.IntegerProperty(default=0)

    stat_games4 = db.IntegerProperty(default=0) # 4 players
    stat_games6 = db.IntegerProperty(default=0) # 6 players
    stat_games8 = db.IntegerProperty(default=0) # 8 players

    stat_kills = db.IntegerProperty()
    stat_luck = db.FloatProperty()

    # 4 players
    stat_place1 = db.IntegerProperty(default=0)
    stat_place2 = db.IntegerProperty(default=0)
    stat_place3 = db.IntegerProperty(default=0)
    stat_place4 = db.IntegerProperty(default=0)

    # 6 players
    stat_6_place1 = db.IntegerProperty(default=0)
    stat_6_place2 = db.IntegerProperty(default=0)
    stat_6_place3 = db.IntegerProperty(default=0)
    stat_6_place4 = db.IntegerProperty(default=0)
    stat_6_place5 = db.IntegerProperty(default=0)
    stat_6_place6 = db.IntegerProperty(default=0)

    # 8 players
    stat_8_place1 = db.IntegerProperty(default=0)
    stat_8_place2 = db.IntegerProperty(default=0)
    stat_8_place3 = db.IntegerProperty(default=0)
    stat_8_place4 = db.IntegerProperty(default=0)
    stat_8_place5 = db.IntegerProperty(default=0)
    stat_8_place6 = db.IntegerProperty(default=0)
    stat_8_place7 = db.IntegerProperty(default=0)
    stat_8_place8 = db.IntegerProperty(default=0)

    @staticmethod
    def getCurrentSeason(prec=0):
        d = datetime.date.today() - datetime.timedelta(days=prec)
        return (d.year - 2011)*12 + d.month

    @staticmethod
    def getSeasonNameById(id):
        if id == 1:
            return _(u'первый сезон')
        elif id >= 2:
            i = (id -1) % 12
            y = 2011 + int(math.floor(id/12))
            if utils.RequestHandlerExt.lang == 'en':
                months = [
                    'january', 'february', 'march',
                    'april', 'may', 'june',
                    'july', 'august', 'september',
                    'october', 'november', 'december']
            else:
                months = [
                    'январь', 'февраль', 'март',
                    'апрель', 'май', 'июнь',
                    'июль', 'август', 'сентябрь',
                    'октябрь', 'ноябрь', 'декабрь']
            return '%s %s' % (months[i], y)

    @staticmethod
    def getCurrentSeasonName(prec=0):
        return StatSeason.getSeasonNameById(StatSeason.getCurrentSeason())

    @staticmethod
    def moveStat(user):
        s = StatSeason()
        s.user = user
        s.season = StatSeason.getCurrentSeason(1) # at first day of month should return previous season

        place = user.getPlaceRange()
        s.place = place[0]
        s.place_range = place[1]

        move_fields = ['score', 'stat_ppg', 'stat_ppg_top',
            'stat_games', 'stat_games4', 'stat_games6', 'stat_games8',
            'stat_place1', 'stat_place2', 'stat_place3', 'stat_place4',
            'stat_6_place1', 'stat_6_place2', 'stat_6_place3', 'stat_6_place4', 'stat_6_place5', 'stat_6_place6',
            'stat_8_place1', 'stat_8_place2', 'stat_8_place3', 'stat_8_place4', 'stat_8_place5', 'stat_8_place6', 'stat_8_place7', 'stat_8_place8'
            ]
        for f in move_fields:
            zero_val = 0
            if type(getattr(user, f))==float:
                zero_val = 0.0
            setattr(s, f, getattr(user, f, zero_val))
            setattr(user, f, zero_val)

        s.put()
        user.put()

    def getSeasonName(self):
        return StatSeason.getSeasonNameById(self.season)
    def isRewarded(self):
        return self.place>0 and self.place <=10
    def getLink(self):
        return '/leaders/%s.html' % self.season;

class Session(db.Model):
    user = db.ReferenceProperty()
    session = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    
    @staticmethod
    def gen_session(user):
        query = db.GqlQuery("SELECT * FROM Session WHERE user=:u", u=user)
        s = query.get()
        if s:
            s.created = datetime.datetime.now()
            s.put()
            return s.session
        else:
            session = hashlib.md5(repr(time.time()) + unicode(random.random())).hexdigest()
            obj = Session()
            obj.user = user
            obj.session = session
            obj.put()
            return session
    
    @staticmethod
    def get_user_by_session(session):
        if str(session).startswith('bot'):
            return userlib.User.auth(userlib.TestUser, {'name': session})
        query = db.GqlQuery("SELECT * FROM Session WHERE session=:s", s=session)
        s = query.get()
        if s:
            return s.user
        else:
            return None
        
class Penalty(db.Model):
    user = db.ReferenceProperty(collection_name='user')
    admin = db.ReferenceProperty(collection_name='admin')
    message = db.StringProperty()
    game_id = db.IntegerProperty()
    penalty_score = db.IntegerProperty()
    penalty_playing_together = db.ReferenceProperty(collection_name='friend')
    applied = db.BooleanProperty()
    on_twisted = db.BooleanProperty(default=False)
    ban_chat = db.BooleanProperty(default=False)
    ban_total = db.BooleanProperty(default=False)
    created = db.DateTimeProperty(auto_now_add=True)
    expired = db.DateTimeProperty()

    def hasExpiration(self):
        return self.ban_chat or self.ban_total or self.penalty_playing_together

    def isExpired(self):
        if self.hasExpiration():
            return self.expired<datetime.datetime.now()

    def isNotExpired(self):
        e =  self.isExpired()
        if e is None:
            return e
        return not e

    def duration(self):
        return self.expired - self.created

    def duration_min(self):
        d = self.expired - self.created
        return int( (d.seconds + d.days*86400) / 60 )

    def asArray(self):
        p = {
            'id': str(self.key().id()),
            'user_id': str(self.user.key().id()),
        }
        if self.penalty_score:
            p['score'] = self.penalty_score
        if self.expired:
            p['expired_in'] = int(time.mktime(self.expired.timetuple()) - time.time())
        if self.penalty_playing_together:
            p['user_id2'] = str(self.penalty_playing_together.key().id())
        if self.ban_chat:
            p['chat'] = True
        if self.ban_total:
            p['total'] = True
        return p

class GameReplay(db.Model):
    game = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    map = db.StringProperty()
    players = db.IntegerProperty(default=4)
    replay = db.BlobProperty()
    abuse = db.BooleanProperty(default=False)

    def link_stats(self, game, players, attempt=0):
        players = int(players)
        stats = Stat.all().filter('game =', game)
        cnt = stats.count(9)
        if cnt == players:
            r = GameReplay.all().filter('game =', game).get()
            if r:
                # set links for the game
                res = stats.fetch(players)
                for s in res:
                    s.rgame = r
                    s.put()
                return True

        # wait, not all stat uploaded yet
        if attempt>20:
            logging.warning('too long time to wait uploading stat for a game: %s players: %s count: %s' % (game, players, cnt))
            return False
        deferred.defer(self.link_stats, game, players, attempt+1, _countdown=5)
        return False


# twisted server communication

TWISTED_WEBDOOR = None

def request_twisted_webdoor(params, _deferred=False):
    global TWISTED_WEBDOOR
    if not TWISTED_WEBDOOR: # lazy init
        TWISTED_WEBDOOR = 'http://' + etc.server() + ':1080/thedoors.php?keyphrase=' + etc.TWISTED_PWD_OUT + '&'
    try:
        err = False
        url = TWISTED_WEBDOOR + urllib.urlencode(params)
        logging.info(url)
        response = urllib2.urlopen(url)
    except urllib2.URLError:
        err = True
    if response.code != 200 or err:
        if _deferred:
            return
        raise Exception("Cannot open url")
    html = response.read()
    return html