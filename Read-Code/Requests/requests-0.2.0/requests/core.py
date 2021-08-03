# -*- coding: utf-8 -*-

"""
    requests.core
    ~~~~~~~~~~~~~

    This module implements the main Requests system.

    :copyright: (c) 2011 by Kenneth Reitz.
    :license: ISC, see LICENSE for more details.
"""

import urllib
import urllib2

__title__ = 'requests'
__version__ = '0.2.0'
__build__ = 0x000200
__author__ = 'Kenneth Reitz'
__license__ = 'ISC'
__copyright__ = 'Copyright 2011 Kenneth Reitz'

AUTOAUTHS = []


class _Request(urllib2.Request):
    """Hidden wrapper around the urllib2.Request object. Allows for manual
    setting of HTTP methods.
    """
    """
    1. _Request 类继承于 urllib2.Request 类
    """
    def __init__(self, url, data=None, headers={}, origin_req_host=None,
                 unverifiable=False, method=None):
        """
        1. 初始化时包含了 url， data， headers， origin_req_host， unverifiable 和
           method 一共 6 个参数， url 为必须参数， 初始化的时候必须拥有， 其余参数为
           可选参数
        2. 使用除 method 参数以外的 5 个参数初始化 urllib2.Request 类
        3. 然后使用 self.method 保存 method， 使其类级别访问
        """
        urllib2.Request.__init__(
            self, url, data, headers, origin_req_host, unverifiable
        )
        self.method = method

    def get_method(self):
        """
        1. 获取请求方法。 如果 self.method 有值， 就返回 self.method， 否则将从
           urllib2.Request 中获取请求方法
        """
        if self.method:
            return self.method

        return urllib2.Request.get_method(self)


class Request(object):
    """The :class:`Request` object. It carries out all functionality of
    Requests. Recommended interface is with the Requests functions.

    """
    """
    1. Request 类包含了所有的请求功能
    2. 请求方法共列出了 5 种， 分别是 GET， HEAD， PUT， POST， DELETE
    """
    _METHODS = ('GET', 'HEAD', 'PUT', 'POST', 'DELETE')

    def __init__(self):
        """
        1. Request 类初始化， 共有 8 个属性
        """
        self.url = None
        self.headers = dict()
        self.method = None
        self.params = {}
        self.data = {}
        self.response = Response()
        self.auth = None
        self.sent = False

    def __repr__(self):
        """
        1. __repr__ 函数会在类执行完毕后执行
        2. 尝试打印类执行完毕后的请求方法， 此处有逻辑问题， 因为 self.method 是一直
           有值的， 因此会一直打印 try 内部的语句， 并不会执行 except 的语句
        """
        try:
            repr = '<Request [%s]>' % (self.method)
        except:
            repr = '<Request object>'
        return repr

    def __setattr__(self, name, value):
        if (name == 'method') and (value):
            if not value in self._METHODS:
                raise InvalidMethod()

        object.__setattr__(self, name, value)

    def _checks(self):
        """Deterministic checks for consistiency."""

        if not self.url:
            raise URLRequired

    def _get_opener(self):
        """ Creates appropriate opener object for urllib2.
        """

        if self.auth:

            # create a password manager
            authr = urllib2.HTTPPasswordMgrWithDefaultRealm()

            authr.add_password(None, self.url, self.auth.username, self.auth.password)
            handler = urllib2.HTTPBasicAuthHandler(authr)
            opener = urllib2.build_opener(handler)

            # use the opener to fetch a URL
            return opener.open
        else:
            return urllib2.urlopen

    def send(self, anyway=False):
        """ Sends the request. Returns True of successfull, false if not.
            If there was an HTTPError during transmission,
            self.response.status_code will contain the HTTPError code.

            Once a request is successfully sent, `sent` will equal True.

            :param anyway: If True, request will be sent, even if it has
            already been sent.
        """
        self._checks()

        success = False

        if self.method in ('GET', 'HEAD', 'DELETE'):
            if (not self.sent) or anyway:

                # url encode GET params if it's a dict
                if isinstance(self.params, dict):
                    params = urllib.urlencode(self.params)
                else:

                    params = self.params

                req = _Request(("%s?%s" % (self.url, params)), method=self.method)

                if self.headers:
                    req.headers = self.headers

                opener = self._get_opener()

                try:
                    resp = opener(req)
                    self.response.status_code = resp.code
                    self.response.headers = resp.info().dict
                    if self.method.lower() == 'get':
                        self.response.content = resp.read()

                    success = True
                except urllib2.HTTPError, why:
                    self.response.status_code = why.code

        elif self.method == 'PUT':
            if (not self.sent) or anyway:

                req = _Request(self.url, method='PUT')

                if self.headers:
                    req.headers = self.headers

                req.data = self.data

                try:
                    opener = self._get_opener()
                    resp = opener(req)

                    self.response.status_code = resp.code
                    self.response.headers = resp.info().dict
                    self.response.content = resp.read()

                    success = True

                except urllib2.HTTPError, why:
                    self.response.status_code = why.code

        elif self.method == 'POST':
            if (not self.sent) or anyway:

                req = _Request(self.url, method='POST')

                if self.headers:
                    req.headers = self.headers

                # url encode form data if it's a dict
                if isinstance(self.data, dict):
                    req.data = urllib.urlencode(self.data)
                else:
                    req.data = self.data

                try:

                    opener = self._get_opener()
                    resp = opener(req)

                    self.response.status_code = resp.code
                    self.response.headers = resp.info().dict
                    self.response.content = resp.read()

                    success = True

                except urllib2.HTTPError, why:
                    self.response.status_code = why.code

        self.sent = True if success else False

        return success


class Response(object):
    """The :class:`Request` object. All :class:`Request` objects contain a
    :class:`Request.response <response>` attribute, which is an instance of
    this class.
    """

    def __init__(self):
        self.content = None
        self.status_code = None
        self.headers = dict()

    def __repr__(self):
        try:
            repr = '<Response [%s]>' % (self.status_code)
        except:
            repr = '<Response object>'
        return repr


class AuthObject(object):
    """The :class:`AuthObject` is a simple HTTP Authentication token. When
    given to a Requests function, it enables Basic HTTP Authentication for that
    Request. You can also enable Authorization for domain realms with AutoAuth.
    See AutoAuth for more details.s

    :param username: Username to authenticate with.
    :param password: Password for given username.
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password


def get(url, params={}, headers={}, auth=None):
    """Sends a GET request. Returns :class:`Response` object.

    :param url: URL for the new :class:`Request` object.
    :param params: (optional) Dictionary of GET Parameters to send with the :class:`Request`.
    :param headers: (optional) Dictionary of HTTP Headers to sent with the :class:`Request`.
    :param auth: (optional) AuthObject to enable Basic HTTP Auth.
    """

    r = Request()

    r.method = 'GET'
    r.url = url
    r.params = params
    r.headers = headers
    r.auth = _detect_auth(url, auth)

    r.send()

    return r.response


def head(url, params={}, headers={}, auth=None):
    """Sends a HEAD request. Returns :class:`Response` object.

    :param url: URL for the new :class:`Request` object.
    :param params: (optional) Dictionary of GET Parameters to send with the :class:`Request`.
    :param headers: (optional) Dictionary of HTTP Headers to sent with the :class:`Request`.
    :param auth: (optional) AuthObject to enable Basic HTTP Auth.
    """

    r = Request()

    r.method = 'HEAD'
    r.url = url
    # return response object
    r.params = params
    r.headers = headers
    r.auth = _detect_auth(url, auth)

    r.send()

    return r.response


def post(url, data={}, headers={}, auth=None):
    """Sends a POST request. Returns :class:`Response` object.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary of POST Data to send with the :class:`Request`.
    :param headers: (optional) Dictionary of HTTP Headers to sent with the :class:`Request`.
    :param auth: (optional) AuthObject to enable Basic HTTP Auth.
    """

    r = Request()

    r.url = url
    r.method = 'POST'
    r.data = data

    r.headers = headers
    r.auth = _detect_auth(url, auth)

    r.send()

    return r.response


def put(url, data='', headers={}, auth=None):
    """Sends a PUT request. Returns :class:`Response` object.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Bytes of PUT Data to send with the :class:`Request`.
    :param headers: (optional) Dictionary of HTTP Headers to sent with the :class:`Request`.
    :param auth: (optional) AuthObject to enable Basic HTTP Auth.
    """

    r = Request()

    r.url = url
    r.method = 'PUT'
    r.data = data

    r.headers = headers
    r.auth = _detect_auth(url, auth)

    r.send()

    return r.response


def delete(url, params={}, headers={}, auth=None):
    """Sends a DELETE request. Returns :class:`Response` object.

    :param url: URL for the new :class:`Request` object.
    :param params: (optional) Dictionary of GET Parameters to send with the :class:`Request`.
    :param headers: (optional) Dictionary of HTTP Headers to sent with the :class:`Request`.
    :param auth: (optional) AuthObject to enable Basic HTTP Auth.
    """

    r = Request()

    r.url = url
    r.method = 'DELETE'
    # return response object

    r.headers = headers
    r.auth = _detect_auth(url, auth)

    r.send()

    return r.response


def add_autoauth(url, authobject):
    """Registers given AuthObject to given URL domain. for auto-activation.
    Once a URL is registered with an AuthObject, the configured HTTP
    Authentication will be used for all requests with URLS containing the given
    URL string.

    Example: ::
        >>> c_auth = requests.AuthObject('kennethreitz', 'xxxxxxx')
        >>> requests.add_autoauth('https://convore.com/api/', c_auth)
        >>> r = requests.get('https://convore.com/api/account/verify.json')
        # Automatically HTTP Authenticated! Wh00t!

    :param url: Base URL for given AuthObject to auto-activate for.
    :param authobject: AuthObject to auto-activate.
    """
    global AUTOAUTHS

    AUTOAUTHS.append((url, authobject))


def _detect_auth(url, auth):
    """Returns registered AuthObject for given url if available, defaulting to
    given AuthObject."""

    return _get_autoauth(url) if not auth else auth


def _get_autoauth(url):
    """Returns registered AuthObject for given url if available.
    """

    for (autoauth_url, auth) in AUTOAUTHS:
        if autoauth_url in url:
            return auth

    return None


class RequestException(Exception):
    """There was an ambiguous exception that occured while handling your request."""


class AuthenticationError(RequestException):
    """The authentication credentials provided were invalid."""


class URLRequired(RequestException):
    """A valid URL is required to make a request."""


class InvalidMethod(RequestException):
    """An inappropriate method was attempted."""
