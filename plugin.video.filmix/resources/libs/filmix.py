# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from __future__ import unicode_literals

from future.utils import PY2, PY3, iteritems, python_2_unicode_compatible
from builtins import range

import os
from base64 import b64decode
import requests
if PY2:
    import cookielib
else:
    import http.cookiejar as cookielib

debug = False


@python_2_unicode_compatible
class APIException(Exception):

    def __init__(self, msg, code=None):
        self.msg = msg
        self.code = code

    def __str__(self):
        return self.msg


@python_2_unicode_compatible
class http_client(object):

    def __init__(self, headers=None, cookie_file=None):
        self._s = requests.Session()

        if cookie_file is not None:
            self._s.cookies = cookielib.LWPCookieJar(cookie_file)
            if os.path.exists(cookie_file):
                self._s.cookies.load(ignore_discard=True, ignore_expires=True)

        self.update(headers)

    def update(self, headers=None):

        if headers is not None and headers:
            self._s.headers.update(headers)

    def _save_cookies(self):
        if isinstance(self._s.cookies, cookielib.LWPCookieJar) \
           and self._s.cookies.filename:
            self._s.cookies.save(ignore_expires=True, ignore_discard=True)
        
    def post(self, url, **kwargs):

        try:
            r = self._s.post(url, **kwargs)
            r.raise_for_status()
        except requests.ConnectionError:
            raise APIException('Connection error')
        except requests.HTTPError as e:
            raise APIException(str(e))

        if debug:
            print('post')
            print('url:', r.url)
            print('content:', r.content)

        self._save_cookies()

        return r

    def get(self, url, **kwargs):

        try:
            r = self._s.get(url, **kwargs)
            r.raise_for_status()
        except requests.ConnectionError:
            raise APIException('Connection error')
        except requests.HTTPError as e:
            raise APIException(str(e))

        if debug:
            print('get')
            print('url:', r.url)
            print('content:', r.content)

        self._save_cookies()

        return r


@python_2_unicode_compatible
class filmix(object):

    APIException = APIException

    def __init__(self, headers=None, cookies=None):
        self._base_url = 'http://filmix.vip/'

        headers = headers or {}
        headers.update({'User-Agent': None,
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'Accept-Encoding': 'gzip',
                        'Connection': 'keep-alive',
                        'X-FX-Token': '',
                        })

        self._client = http_client(headers, cookies)

    def _post(self, url, params=None, **kwargs):
        url = self._base_url + url
        r = self._client.post(url, params=params, **kwargs)
        
        return r
        
    def _get(self, url, params=None, **kwargs):
        url = self._base_url + url
        r = self._client.get(url, params=params, **kwargs)
        
        return r

    @staticmethod
    def decode_link(link):
    
        tmp_a = 'y,5,U,4,e,i,6,d,7,N,J,g,t,G,2,V,l,B,x,f,s,Q,1,H,z,='.split(',')
        tmp_b = 'M,X,w,R,3,m,8,0,T,a,u,Z,p,D,b,o,k,Y,n,v,I,L,9,W,c,r'.split(',')
        a_length = len(tmp_a);
        for  i in range(0, a_length, 1):
            link = link.replace(tmp_b[i], '___').replace(tmp_a[i], tmp_b[i]).replace('___', tmp_a[i])
        return b64decode(link).decode('utf8')

    def _extract_json(self, r):
        try:
            j = r.json()
        except ValueError as err:
            raise APIException(err)

        if isinstance(j, dict) \
          and j.get('error') is not None:
            if j['error'].get('user_message') is not None:
                raise self.APIException(j['error']['user_message'], j['error']['code'])
            else:
                raise self.APIException(j['error']['message'], j['error']['code'])
        return j

    def _get_profile(self, data=None):
        url = 'android.php?get_profile'

        r = self._post(url, data=data)
        j = self._extract_json(r)

        if isinstance(j, dict):
            result = j['user_data']
        else:
            result = {}

        result.update({'X-FX-Token': r.headers.get('X-FX-Token', ''),
                       })
            
        return result

    def login(self, _login, _password):
        data = {'login_name': _login,
                'login_password': _password,
                'login': 'submit',
                }

        return self._get_profile(data)

    def user_data(self):
 
        return self._get_profile()
        
    def _get_items(self, u_params, page=1, page_params=None, **kwargs):
        url = 'android.php'

        params = kwargs or {}

        per_page = params.get('per_page', '15')

        if page > 1:
            u_params['cstart'] = page

        cookies = {'per_page_news': per_page,
                   }

        r = self._get(url, u_params, cookies=cookies)
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

    def get_catalog_items(self, orderby='', orderdir='', section=996, page=1, filter='', **kwargs):

        if section == 996:
            u_params = {'orderby': orderby,
                        'orderdir': orderdir,
                        }
        else:
            u_params = {'do': 'cat',
                        'category': '',
                        'orderby': orderby,
                        'orderdir': orderdir,
                        'requested_url': 'filters/s{0}{1}{2}'.format(section, '-' if filter else '', filter)
                        }
        
        page_params = {'orderby': orderby,
                       'orderdir': orderdir,
                       }
        
        return self._get_items(u_params, page, page_params, **kwargs)

    def get_movie_info(self, newsid='', alt_name=''):
        url = 'android.php'
        u_params = {'newsid': newsid,
                    'seourl': alt_name,
                    }
        
        r = self._get(url, u_params)
        j = self._extract_json(r)

        return j
        
    def get_search_catalog(self, keyword, page=1, **kwargs):

        u_params = {'do': 'search',
                    'story': keyword,
                    }

        return self._get_items(u_params, **kwargs)

    def get_favorites_items(self, page=1, **kwargs):
        u_params = {'do': 'favorites',
                    }

        return self._get_items(u_params, page, {}, **kwargs)

    def get_watch_later_items(self, page=1, **kwargs):
        u_params = {'do': 'watch_later',
                    }

        return self._get_items(u_params, page, {}, **kwargs)

    def get_history_items(self, page=1, **kwargs):
        u_params = {'do': 'last_seen',
                    }

        return self._get_items(u_params, page, {}, **kwargs)

    def get_popular_items(self, page=1, **kwargs):
        u_params = {'do': 'popular',
                    }

        return self._get_items(u_params, page, {}, **kwargs)

    def get_top_views_items(self, page=1, **kwargs):
        u_params = {'do': 'top_views',
                    }

        return self._get_items(u_params, page, {}, **kwargs)
         
    def get_filter(self, scope, type):
        url = 'engine/ajax/get_filter.php'

        u_params = {'scope': scope,
                    'type': type,
                    }

        r = self._post(url, u_params)
        j = self._extract_json(r)

        return j
