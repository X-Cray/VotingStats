import re
import urllib
import logging
from datetime import datetime
from urllib import FancyURLopener
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import urlfetch
from common import *
from data import *
from proxy import *

page_regex = re.compile("<a href='index.php(.page=\d+)'>\d+</a>")
proxy_id_regex = re.compile("javascript:wnd_small.'(.action=get&id=\d+)'.")
proxy_address_regex = re.compile("<TD>HTTP.S.</TD><TD><B>([\w\.]+)\s*:\s*(\d+)</B></TD>")
base_url = "http://proxy.insorg.org/ru/index.php"
request_headers = {
	"User-Agent": "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.237 Safari/534.10",
	"Accept": "application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
	"Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
	"Accept-Encoding": "gzip,deflate,sdch",
	"Accept-Language": "en-US,en;q=0.8",
	"Referer": base_url
}

class InsorgGrabber(ProxyBase):
	sort_method = None
	base_cookie = None
	cookie = None

	def __init__(self, base_ccokie, sort_method):
		self.base_cookie = base_ccokie
		self.sort_method = sort_method

	def get(self):
		settings = get_settings()
		if (settings["grabber_enabled"]):
			wakeup = memcache.get(cache_grabber_wakeup)

			if not wakeup or datetime.now() > wakeup:
				memcache.set(cache_grabber_wakeup, None)
				memcache.set(cache_grabber_status, "working")

				page_paths = self.__get_page_paths(base_url)

				if page_paths:
					page_paths = [""] + page_paths
			
					for path in page_paths:
						proxy_ids = self.__get_proxy_ids("%s%s" % (base_url, path))

						if proxy_ids:
							for proxy_id in proxy_ids:
#								proxies_count = 0
								if not self.proxies_contain_tag(proxy_id):
									proxy_address = self.__get_proxy_address("%s%s" % (base_url, proxy_id))
#									proxies_count = proxies_count + 1

									if proxy_address:
										logging.info("Saving proxy %s to database" % proxy_address)
										self.save_proxy(proxy_address, "http", proxy_id)
										self.__log_proxy()
									else:
										logging.warning("Got no proxy address for %s" % proxy_id)
										misses = memcache.get(cache_grabber_misses) or 0;

										if misses > 3:
											memcache.set(cache_grabber_wakeup, datetime.now() + halfhour)
											memcache.set(cache_grabber_status, "sleeping")
											memcache.set(cache_grabber_misses, 0)
										else:
											memcache.set(cache_grabber_misses, misses + 1)

#									if proxies_count < 2:
#										continue

									return
		else:
			memcache.set(cache_grabber_status, "off")

	def __get_page_paths(self, proxies_page_url):
		proxies_page = self.__load_cookie_page(proxies_page_url)

		if proxies_page:
			return page_regex.findall(proxies_page)

	def __get_proxy_ids(self, proxies_page_url):
		proxies_page = self.__load_page(proxies_page_url)

		if proxies_page:
			return proxy_id_regex.findall(proxies_page)

	def __get_proxy_address(self, proxy_page_url):
		proxy_page = self.__load_page(proxy_page_url)
		
		if proxy_page:
			address = proxy_address_regex.search(proxy_page)
			if address:
				return "%s:%s" % (address.group(1), address.group(2))

	def __load_cookie_page(self, url):
		params = urllib.urlencode({ "flt[country][UA]": "UA", "flt[order]": self.sort_method })
		headers = {
			"Content-Type": "application/x-www-form-urlencoded",
			"Cookie": self.base_cookie
		}

		for key, value in request_headers.iteritems():
			headers[key] = value

		res = urlfetch.fetch(url=url, payload=params, method=urlfetch.POST, headers=headers, deadline=30)
		self.cookie = "%s; %s" % (self.base_cookie, res.headers["set-cookie"].partition(";")[0])
		logging.debug("Using cookie: %s" % self.cookie)
		#logging.debug("Received page: %s" % res.content)
		return res.content

	def __load_page(self, url):
		res = None
		body = None
		opener = FancyURLopener()

		# Clear default User-Agent header which is defined in addheaders.
		opener.addheaders = []
		for key, value in request_headers.iteritems():
			opener.addheader(key, value)
		opener.addheader("Cookie", self.cookie)

		try:
			res = opener.open(url)
			body = res.read()
		except IOError, error:
			logging.error(error.strerror)
		finally:
			res and res.close()

		#logging.debug("Received page: %s" % body)
		return body

	def __log_proxy(self):
		proxies_log = memcache.get(cache_proxies_log_key) or []
		if not hasattr(proxies_log, "append"):
			proxies_log = []

		proxies_log.append(datetime.now())
		last_hour = datetime.now() - onehour
		if not memcache.set(cache_proxies_log_key, [date for date in proxies_log if date > last_hour]):
			logging.error("Failed to log proxy")
