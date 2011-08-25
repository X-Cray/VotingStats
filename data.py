import logging
from google.appengine.ext import db
from google.appengine.api import memcache

class PhotoInfo(db.Model):
	photo_id = db.IntegerProperty()
	date = db.DateTimeProperty(auto_now_add=True)
	votes_count = db.IntegerProperty()

class ProxyInfo(db.Model):
	fails = db.IntegerProperty(default=0)
	tag = db.StringProperty()
	type = db.StringProperty()
	date = db.DateTimeProperty(auto_now_add=True)
	last_usage = db.DateTimeProperty()

class VoteArrangement(db.Model):
	link = db.StringProperty()
	referer = db.StringProperty()
	proxy = db.StringProperty()
	type = db.StringProperty()
	browser = db.StringProperty()

class Settings(db.Model):
	grabber_enabled = db.BooleanProperty(default=True)
	voter_enabled = db.BooleanProperty(default=True)
	tasks_per_minute = db.IntegerProperty(default=2)

class PhotoVote():
	def __init__(self, date, intdate, vote):
		self.date = date
		self.intdate = intdate
		self.vote = vote

class Photo():
	def __init__(self, id, votes):
		self.id = id
		self.votes = votes

cache_settings_key = "settings"

def get_settings_dictionary(settings):
	return {
		"grabber_enabled": settings.grabber_enabled,
		"voter_enabled": settings.voter_enabled,
		"tasks_per_minute": settings.tasks_per_minute
	}

def get_settings():
	settings = memcache.get(cache_settings_key)
	if settings:
		return settings
	else:
		settings_dict = get_settings_dictionary(Settings.get_or_insert(cache_settings_key))
		if not memcache.set(cache_settings_key, settings_dict):
			logging.error("Memcache set failed.")
		return settings_dict

def set_settings(settings_dict):
	settings_dict["grabber_enabled"] = settings_dict["grabber_enabled"] == "1"
	settings_dict["voter_enabled"] = settings_dict["voter_enabled"] == "1"
	settings_dict["tasks_per_minute"] = int(settings_dict["tasks_per_minute"])
	set_settings_internal(settings_dict)
	if not memcache.set(cache_settings_key, settings_dict):
		logging.error("Memcache set failed.")
	
def set_settings_internal(settings_dict):
	settings = Settings.get_or_insert(cache_settings_key)
	settings.grabber_enabled = settings_dict["grabber_enabled"]
	settings.voter_enabled = settings_dict["voter_enabled"]
	settings.tasks_per_minute = settings_dict["tasks_per_minute"]
	settings.save()
