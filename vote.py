import os
import re
import sys
import urllib
import logging
from datetime import datetime
from google.appengine.api.taskqueue import Task
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import urlfetch_errors
from django.utils import simplejson as json
from common import *
from data import *

header_regex = re.compile("([\w\-]+)\s*:\s*(.+)")

# Settings
links_to_open = [
#	("http://lavina.dp.ua/fcvote.php?action=like&pid=103", "http://lavina.dp.ua/fotoConcurs.php?pid=103"),
#	("http://lavina.dp.ua/fcvote.php?action=like&pid=179", "http://lavina.dp.ua/fotoConcurs.php?pid=179")
	("http://lavina.dp.ua/fcvote.php?action=like&pid=27", "http://lavina.dp.ua/fotoConcurs.php?pid=27"),
	("http://lavina.dp.ua/fcvote.php?action=like&pid=28", "http://lavina.dp.ua/fotoConcurs.php?pid=28")
]
browsers_filename = "browsers.txt"

class Voter(webapp.RequestHandler):
	def post(self):
		self.__open_link(self.request.get("link"), self.request.get("referer"), self.request.get("proxy"), self.request.get("type"), self.request.get("browser"))

	def __open_link(self, link, referer, proxy, type, browser):
		"""Opens given link using given proxy in the form "address:port" with custom headers dictionary"""
		logging.debug("Opening %s via %s" % (link, proxy))

		params = urllib.urlencode({ "link": link, "referer": referer, "proxy": proxy, "type": type, "browser": browser })
		time_elapsed = None
		try:
			time_start = datetime.now()
			res = urlfetch.fetch(url="http://ips.leanaorders.com", payload=params, method=urlfetch.POST, headers={"Content-Type": "application/x-www-form-urlencoded"}, deadline=30)
			time_elapsed = datetime.now() - time_start
			response_dct = json.loads(res.content)
			if response_dct.has_key("status") and response_dct.has_key("length") and response_dct.has_key("error"):
				logging.info("--> %s. Received %d chars. Took %s seconds (via %s [%s]). Error: '%s'" % (response_dct["status"], response_dct["length"], time_elapsed.seconds, proxy, type, response_dct["error"]))
				if response_dct["status"] == 200:
					self.__update_proxy_usage(proxy)
					self.__log_vote()
				else:
					self.__delete_proxy(proxy)
			else:
				logging.error("Unexpected output from voter: %s" % res.content)
		except:
			if not time_elapsed:
				time_elapsed = datetime.now() - time_start
			
			exc = sys.exc_info()
			logging.error("--> [!] %s:%s. Took %s seconds (via %s [%s])" % (exc[0], exc[1], time_elapsed.seconds, proxy, type))
			
			# If there was download error the proxy probably failed.
			if exc[0] == urlfetch_errors.DownloadError:
				self.__delete_proxy(proxy)

	def __log_vote(self):
		votes_log = memcache.get(cache_votes_log_key) or []
		if not hasattr(votes_log, "append"):
			votes_log = []

		votes_log.append(datetime.now())
		last_hour = datetime.now() - onehour

		if not memcache.set(cache_votes_log_key, [date for date in votes_log if date > last_hour]):
			logging.error("Failed to log vote")

	def __update_proxy_usage(self, proxy):
		db.run_in_transaction(self.__update_proxy_usage_internal, proxy)

	def __update_proxy_usage_internal(self, proxy):
		saved_proxy = ProxyInfo.get_by_key_name(proxy)
		if saved_proxy:
			saved_proxy.fails = 0
			saved_proxy.last_usage = datetime.now()
			saved_proxy.save()

	def __delete_proxy(self, proxy):
		db.run_in_transaction(self.__delete_proxy_internal, proxy)

	def __delete_proxy_internal(self, proxy):
		saved_proxy = ProxyInfo.get_by_key_name(proxy)
		if saved_proxy:
			if saved_proxy.fails > 2:
				now = datetime.now()
				saved_proxy.delete()
				logging.warning("Deleting proxy %s which lived for %d hours (%s -- %s)" % (proxy, (now - saved_proxy.date).seconds / 3600, saved_proxy.date, now))
			else:
				saved_proxy.fails = saved_proxy.fails + 1
				saved_proxy.last_usage = datetime.now()
				saved_proxy.save()
				logging.warning("Proxy %s failed %d times" % (proxy, saved_proxy.fails))

class VoteArranger(webapp.RequestHandler):
	def get(self):
		settings = get_settings()
		if (settings["voter_enabled"]):
			arrangements = self.__get_arrangements(settings["tasks_per_minute"])
			if arrangements:
				for arrangement in arrangements:
					task = Task(url="/vote-photo", params={
						"link": arrangement.link,
						"referer": arrangement.referer,
						"proxy": arrangement.proxy,
						"type": arrangement.type,
						"browser": arrangement.browser
					})
					task.add("vote")
					self.__delete_arrangement(arrangement)
			else:
				proxies = self.__get_proxies()
				browsers = self.__get_browsers(browsers_filename)
				self.__arrange_votes(links_to_open, self.__map_browsers(proxies, browsers))

	def __get_arrangements(self, tasks_count):
		return VoteArrangement.all().fetch(tasks_count)

	def __get_proxies(self):
		# Use proxies which have not been used during past hour.
		return [(p.key().name(), p.type) for p in ProxyInfo.gql("WHERE last_usage < :1", datetime.now() - onehour)]

	def __get_browsers(self, filename):
		headers, browsers = {}, []
		f = open(os.path.join(os.path.dirname(__file__), filename), "r")

		for line in f:
			header = header_regex.search(line)

			if header:
				name, value = header.group(1).strip(), header.group(2).strip()
				headers[name] = value
			else:
				browsers.append(headers)
				headers = {}

		f.close()
		return browsers

	def __map_browsers(self, proxies, browsers):
			mappings, counter = [], 0

			for proxy in proxies:
				if len(browsers) <= counter:
					counter += 1
				else:
					counter = 0

				mappings.append((proxy, browsers[counter]))

			logging.debug("Mapped %d proxies to %d browser configurations" % (len(proxies), len(browsers)))
			return mappings
	
	def __arrange_votes(self, links, mappings):
		for proxy, browser in mappings:
			for link in links:
				self.__save_arrangement(link[0], link[1], proxy[0], proxy[1], json.dumps(browser))
		self.__log_arrangement(len(mappings) * len(links))

	def __log_arrangement(self, count):
		memcache.set(cache_vote_arrangements_log_key, count)

	def __delete_arrangement(self, arrangement):
		db.run_in_transaction(self.__delete_arrangement_internal, arrangement)

	def __delete_arrangement_internal(self, arrangement):
		arrangement.delete()

	def __save_arrangement(self, link, referer, proxy, type, browser):
		db.run_in_transaction(self.__save_arrangement_internal, link, referer, proxy, type, browser)

	def __save_arrangement_internal(self, link, referer, proxy, type, browser):
		VoteArrangement(link=link, referer=referer, proxy=proxy, type=type, browser=browser).put()
