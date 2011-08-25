from django.utils import simplejson as json
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext import db
from common import *
from data import *

class SettingsManager(webapp.RequestHandler):
	def get(self):
		self.response.out.write(json.dumps(get_settings()))
		
	def post(self):
		settings = self.request.get("settings")
		if settings:
			set_settings(json.loads(settings))

class StatusViewer(webapp.RequestHandler):
	def get(self):
		votes_last_hour, proxies_last_hour = "n/a", "n/a"
		
		votes_log = memcache.get(cache_votes_log_key)
		proxies_log = memcache.get(cache_proxies_log_key)
		vote_arrangements_log = memcache.get(cache_vote_arrangements_log_key)
		
		if votes_log:
			votes_last_hour = len(votes_log)
		
		if proxies_log:
			proxies_last_hour = len(proxies_log)
	
		photo_27 = PhotoInfo.gql("WHERE photo_id = :1 ORDER BY date DESC", 27).get()
		photo_28 = PhotoInfo.gql("WHERE photo_id = :1 ORDER BY date DESC", 28).get()
		photo_61 = PhotoInfo.gql("WHERE photo_id = :1 ORDER BY date DESC", 61).get()

		self.response.out.write(json.dumps({
#			"photo_infos_in_db": PhotoInfo.all().count(300000),
			"difference": max(photo_27.votes_count, photo_28.votes_count) - photo_61.votes_count,
			"votes_last_hour": votes_last_hour,
			"jobs_last_time": vote_arrangements_log,
			"jobs_in_db": VoteArrangement.all().count(),
			"grabber_status": memcache.get(cache_grabber_status),
			"proxies_last_hour": proxies_last_hour,
			"proxies_in_db": ProxyInfo.all().count()
		}))

class GraphViewer(webapp.RequestHandler):
	def get(self):
		data = memcache.get(cache_data_key_template % cache_index_key)
		self.response.out.write(data)
