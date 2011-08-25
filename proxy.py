from datetime import datetime
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext import db
from data import *

last_usage_default = datetime(2010, 01, 01)

class ProxyBase(webapp.RequestHandler):
	def proxies_contain_tag(self, tag):
		return ProxyInfo.gql("WHERE tag = :1", tag).count(1) == 1

	def proxies_contain_key(self, proxy):
		return ProxyInfo.get_by_key_name(proxy)

	def save_proxy(self, proxy_address, type, tag):
		db.run_in_transaction(self.__save_proxy_internal, proxy_address, type, tag)

	def __save_proxy_internal(self, proxy_address, type, tag):
		ProxyInfo(key_name=proxy_address, type=type, tag=tag, last_usage=last_usage_default).put()
