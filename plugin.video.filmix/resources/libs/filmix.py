# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

from future.utils import PY26, PY3, iteritems, python_2_unicode_compatible
from builtins import range

import os
import ssl
import math
import random
import requests
from base64 import b64decode
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context
import filmixcert

__all__ = ['FilmixClient', 'FilmixError']


class FilmixError(Exception):

    def __init__(self, message, code=None):
        self.message = message
        self.code = code

        super(FilmixError, self).__init__(self.message)


class FilmixAdapter(HTTPAdapter):

    _filmix_ciphers = 'DEFAULT@SECLEVEL=0'

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=self._filmix_ciphers)
        kwargs['ssl_context'] = context
        return super(FilmixAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=self._filmix_ciphers)
        kwargs['ssl_context'] = context
        return super(FilmixAdapter, self).proxy_manager_for(*args, **kwargs)


@python_2_unicode_compatible
class FilmixClient(object):

    _base_url = 'https://app.filmix.vip:8044/'

    def __init__(self):

        headers = {'User-Agent': None,
                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   }

        self._client = requests.Session()
        self._client.headers.update(headers)

        certificate = filmixcert.certificate()
        plainkey = filmixcert.plainkey()

        self._client.cert = (certificate, plainkey)
        self._client.verify = False  # certificate

        if not PY26 \
          and ssl.OPENSSL_VERSION_INFO >= (1, 1, 0):
            try:
                adapter = FilmixAdapter()
            except ssl.SSLError as e:
                print('OpenSSL info: {0}'.format(ssl.OPENSSL_VERSION))
                print('Error: {0}'.format(e))
            else:
                self._client.mount(self._base_url, adapter)

        self._user_dev_id = None
        self._user_dev_name = None
        self._user_dev_token = None
        self._user_dev_vendor = None

    def __str__(self):
        return '<FilmixClient>'

    def _add_device_info(self, params):
        params = params or {}
        params['user_dev_id'] = self._user_dev_id
        params['user_dev_name'] = self._user_dev_name
        params['user_dev_token'] = self._user_dev_token
        params['user_dev_vendor'] = self._user_dev_vendor
        
        return params

    def _get(self, url, params=None, *args, **kwargs):
        params = self._add_device_info(params)
        
        return self._client.get(url, params=params, *args, **kwargs)

    def _post(self, url, data=None, *args, **kwargs):
        data = self._add_device_info(data)
        
        return self._client.post(url, data=data, *args, **kwargs)

    @staticmethod
    def decode_link(link):

        tmp_a = 'u,5,Y,I,E,4,7,D,6,G,j,n,2,g,T,b,L,v,S,F,X,h,1,q,=,Z'.split(',')
        tmp_b = 'W,x,m,M,3,r,t,0,8,z,U,A,B,d,P,y,K,O,i,V,N,w,9,l,R,C'.split(',')
        a_length = len(tmp_a);
        for  i in range(0, a_length, 1):
            link = link.replace(tmp_b[i], '___').replace(tmp_a[i], tmp_b[i]).replace('___', tmp_a[i])
        return b64decode(link).decode('utf8')

    def _extract_json(self, r):
        try:
            j = r.json()
        except ValueError as e:
            raise FilmixError(e)

        if isinstance(j, dict) \
          and j.get('error') is not None:
            if j['error'].get('user_message') is not None:
                raise FilmixError(j['error']['user_message'], j['error']['code'])
            else:
                raise FilmixError(j['error']['message'], j['error']['code'])
        return j

    def _get_profile(self, data=None):
        url = self._base_url + 'android.php?get_profile'

        r = self._client.post(url, data=data)
        j = self._extract_json(r)

        if isinstance(j, dict):
            result = j['user_data']
        else:
            result = {}

        result.update({'X-FX-Token': r.headers.get('X-FX-Token', ''),
                       })

        return result

    @staticmethod
    def create_dev_id():

        result = ''
        charsets = '0123456789abcdef'
        while(len(result) < 16):
            index = int(math.floor(random.random() * 15))
            result = result + charsets[index]
        return result

    def token_request(self):
        url = self._base_url + 'adgvn/token_request'

        r = self._get(url)
        j = self._extract_json(r)

        return j
        
    def set_videoserver(self, vs_schg):
        url = self._base_url + 'android.php'

        data = {'vs_schg': vs_schg,
                }

        r = self._post(url, data=data)
        j = self._extract_json(r)

        return j

    def user_data(self):
        url = self._base_url + 'android.php?user_profile'

        r = self._get(url)
        j = self._extract_json(r)

        if isinstance(j, dict):
            result = j['user_data']
        else:
            result = {}
        
        return result

    def _get_items(self, u_params, page=1, page_params=None, **kwargs):
        url = self._base_url + 'android.php'

        params = kwargs or {}

        per_page = params.get('per_page', '15')

        if page > 1:
            u_params['cstart'] = page

        cookies = {'per_page_news': per_page,
                   }

        r = self._get(url, params=u_params, cookies=cookies)
        j = self._extract_json(r) or []

        if page_params is not None:
            pages = {'prev': {'page': page - 1} if page > 1 else None,
                     'next': {'page': page + 1} if int(per_page) == len(j) else None,
                     }
            if pages['prev'] is not None: pages['prev'].update(page_params)
            if pages['next'] is not None: pages['next'].update(page_params)
        else:
            pages = {'prev': None,
                     'next': None,
                     }

        result = {'count': len(j),
                  'items': j,
                  'pages': pages,
                  }

        return result

    def get_catalog_items(self, orderby='', orderdir='', section=996, page=1, filters='', **kwargs):

        if section == 996:
            u_params = {'orderby': orderby,
                        'orderdir': orderdir,
                        }
        else:
            filter_items = filters.split('-') if filters else []
            filter_items.append('s{0}'.format(section))

            u_params = {'do': 'cat',
                        'category': '',
                        'orderby': orderby,
                        'orderdir': orderdir,
                        'requested_url': 'filters/{0}'.format('-'.join(filter_items))
                        }

        page_params = {'orderby': orderby,
                       'orderdir': orderdir,
                       }

        if filters:
            page_params['filters'] = filters

        return self._get_items(u_params, page, page_params, **kwargs)

    def get_movie_info(self, newsid='', alt_name=''):
        url = self._base_url + 'android.php'
        u_params = {'newsid': newsid,
                    'seourl': alt_name,
                    }

        r = self._get(url, params=u_params)
        j = self._extract_json(r)

        return j

    def get_search_catalog(self, keyword, page=1, **kwargs):

        params = {'do': 'search',
                  'story': keyword,
                  }

        return self._get_items(params, **kwargs)

    def get_favorites_items(self, page=1, **kwargs):
        params = {'do': 'favorites',
                  }

        return self._get_items(params, page, {}, **kwargs)

    def get_watch_later_items(self, page=1, **kwargs):
        params = {'do': 'watch_later',
                 }

        return self._get_items(params, page, {}, **kwargs)

    def get_history_items(self, page=1, **kwargs):
        params = {'do': 'last_seen',
                  }

        return self._get_items(params, page, {}, **kwargs)

    def get_popular_items(self, page=1, **kwargs):
        params = {'do': 'popular',
                  }

        return self._get_items(params, page, {}, **kwargs)

    def get_top_views_items(self, page=1, **kwargs):
        params = {'do': 'top_views',
                  }

        return self._get_items(params, page, {}, **kwargs)

    def get_filter(self, scope, filter_id=None):
        url = self._base_url + 'engine/ajax/get_filter.php'

        data = {'scope': scope,
                  }
        if filter_id is not None:
            data['type'] = filter_id

        r = self._post(url, data=data)
        j = self._extract_json(r)

        return j

    def set_favorite(self, fav_id, value):
        url = self._base_url + 'android.php?favorite'

        params = {'fav_id': fav_id,
                  'action': 'plus' if value else 'minus',
                  'skin': 'Filmix',
                  'alert': '0',
                  }

        self._get(url, params=params)

    def set_watch_later(self, post_id, value):
        url = self._base_url + 'android.php'

        data = {'post_id': post_id,
                'action': 'add' if value else 'rm',
                'deferred': True,
                }

        self._post(url, data=data)

    def add_watched(self, post_id, season=None, episode=None, translation=None):
        url = self._base_url + 'android.php'

        data = {'add_watched':'true',
                'id': post_id,
                }

        if season is not None:
            data['season'] = season

        if episode is not None:
            data['episode'] = episode

        if translation is not None:
            data['translation'] = translation

        self._post(url, data=data)
