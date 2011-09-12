import time,random
import hashlib
import urllib

class VKRequestException(Exception):
    pass

class VKRequest:

    def __init__(self, app_id, secret=None, viewer_id=None, sid=None, version='3.0'):
        self.app_id = app_id
        self.secret = secret
        self.viewer_id = viewer_id
        self.sid = sid # it's session
        self.version = version
    
    def requireViewer(self):
        if not self.viewer_id:
            raise VKRequestException('viewer_id should be set')

    def request(self, params):
        url = 'http://api.vkontakte.ru/api.php?'
        params.update({
            'api_id': self.app_id,
            'v': self.version,
            'timestamp': int(time.time()),
            'format': 'json',
            'random': random.randint(1, 10000),
        })
        ks = params.keys()
        ks.sort()
        sig = ''
        for k in ks:
            s = params[k]
            if type(s) == int or type(s)==long:
                s = str(s)
            s = s.encode('utf8')
            params[k] = s
            sig += k + '=' + s
        sig += self.secret
        md5 = hashlib.md5()
        md5.update(sig)
        params['sig'] = md5.hexdigest()
        url += urllib.urlencode(params)
        return url

    def saveAppStatus(self, status):
        if len(status) > 32 or len(status) == 1:
            raise VKRequestException('Status text should be between 0 and 32 symbols in length')
        self.requireViewer()
        return self.request({
            'method': 'secure.saveAppStatus',
            'uid': self.viewer_id,
            'status': status
        })

    def saveNotification(self, uids, text):
        return self.request({
            'method': 'secure.sendNotification',
            'uids': uids,
            'message': text
        })

    def isAppUser(self, uid):
        return self.request({
            'method': 'isAppUser',
            'uid': uid
        })

