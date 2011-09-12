import os
import datetime
import time
import logging
from libs.gsfoid import utils

# twisted server communication passwords

TWISTED_PWD_IN = ''
TWISTED_PWD_OUT = ''

# data sync password

SYNC_PASS = ''

# Vars

LANG = ''
HOST = ''
HOST_SCHEME = 'http'

# Consts

ENV_DEV = 'dev'
ENV_PROD = 'prod'

LANG_RU = 'ru'
LANG_EN = 'en'
LANGS = [LANG_EN, LANG_RU]

CONF = {
    # debug
    'riskgame2-auth.ru': {
        'twisted': 'riskgame2-auth.ru',
        'default_lang': LANG_RU,
        'map_key': 'ABQIAAAAui_7Y07mYWmpVRmQU7OxuBTrfqN5V1_7dairTg0GzDwk-nZNGhR-iL6ryJ6N3dD19Hbheh5ztbySMg'
    },
    'riskgame2-auth.com': {
        'twisted': 'riskgame2-auth.ru',
        'default_lang': LANG_EN,
        'map_key': 'ABQIAAAAd2TuQ6CRyCvvS1lgERdHtxQ498EceI3RBR-bQqVsj5-ZLzbqMBQSaubFS_7et-OwanjZEqMKtvl7pA',
    },

    # production
    'www.vkubiki.ru': {
        'twisted': 'aurora.vkubiki.ru',
        'default_lang': LANG_RU,
        'map_key': 'ABQIAAAAui_7Y07mYWmpVRmQU7OxuBQA6I_1BLMjIsGbqbq-YWxB8BFXyxR8qqKNC4MsGwEcaMsDuHKjhTOK_Q',
    },
    'www.dicefield.com': {
        'twisted': 'aurora.vkubiki.ru',
        'default_lang': LANG_EN,
        'map_key': 'ABQIAAAAd2TuQ6CRyCvvS1lgERdHtxRIF2e8Nn1ZWqwP2vri63LtwKtN-RRsBUDVN6gZVfFtjQgnLr-UEuhwbA',
    },
    'go-dice.appspot.com': {
        'twisted': 'aurora.vkubiki.ru',
        'default_lang': LANG_EN,
        'map_key': [
            'ABQIAAAAui_7Y07mYWmpVRmQU7OxuBSloFbl8GdXEdmovu4UjX4lsvmlshQlXUhaczEWaU_mW61PjFvzME0gIA', # http
            'ABQIAAAAui_7Y07mYWmpVRmQU7OxuBQrP_Z8231gxDw_oDu4SypIUZac5BSrVw-Ps6x5ioBWVgo8VrByFdrhzw'  # https
        ]
    }
}

def get_env():
    if ('SERVER_SOFTWARE' in os.environ) and os.environ['SERVER_SOFTWARE'].startswith('Development'):
        return ENV_DEV
    else:
        return ENV_PROD

def server():
    global HOST
    return CONF[HOST]['twisted']

def gserver():
    return HOST

def detect_language(this):
    global LANG, HOST, HOST_SCHEME

    # save host
    if 'Host' in this.this_request.headers:
        HOST = this.this_request.headers['Host']
    if 'Scheme' in this.this_request.headers:
        HOST_SCHEME = this.this_request.headers['Scheme']

    # detect lang
    # from request param
    if this.this_request.get('lang') and (this.this_request.get('lang') in [LANG_EN, LANG_RU]):
        LANG = this.this_request.get('lang')

        d = datetime.datetime.now() + datetime.timedelta(days=180)
        utils.Cookie.set('lang', LANG, time.strftime('%a, %d-%b-%Y %H:%M:%S GMT', d.timetuple()))

    # from cookie
    elif utils.Cookie.get('lang'):
        l = utils.Cookie.get('lang')
        if l in LANGS:
            LANG = l
        else:
            LANG = LANG_EN

        d = datetime.datetime.now() + datetime.timedelta(days=180)
        utils.Cookie.set('lang', LANG, time.strftime('%a, %d-%b-%Y %H:%M:%S GMT', d.timetuple()))

    # by default
    else:
        LANG = CONF[HOST]['default_lang']

    return LANG

def map_key():
    global HOST
    if type(CONF[HOST]['map_key']) == list:
        if HOST_SCHEME=='http':
            return CONF[HOST]['map_key'][0]
        else:
            return CONF[HOST]['map_key'][1]
    else:
        return CONF[HOST]['map_key']
