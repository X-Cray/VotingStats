import os
import logging
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from datetime import date
from time import mktime
from common import *
from utils import *
from data import *

class MainPage(webapp.RequestHandler):
	def get(self):
		today = date.today()
		yesterday = today - oneday
		self.__get_index_cached(yesterday, today)

	def post(self):
		date_start = None
		date_end = None
		try:
			date_start = parse_date(self.request.get("date_start"))
			date_end = parse_date(self.request.get("date_end"))
			self.__get_index_cached(date_start, date_end, False)
		except:
			self.get()

	def __get_index_cached(self, date_start, date_end, is_index=True):
		cache_key = cache_index_key
		cache_time = cache_index_time
		
		if not is_index:
			cache_key = "%s-%s" % (date_start, date_end)
			cache_time = cache_permanent_time

		page = memcache.get(cache_key)
		if not page:
			page, data = self.__get_index(date_start, date_end)
			if not memcache.set(cache_key, page, cache_time):
				logging.error("Memcache set failed.")
			if not memcache.set(cache_data_key_template % cache_key, data, cache_time):
				logging.error("Memcache set failed.")

		self.response.out.write(page)

	def __append_template_photo(self, template_photos, photo_id, photo_votes):
		if len(photo_votes) > 1: # Do not create single-dot lines.
			template_photos.append(Photo(
				photo_id,
				photo_votes
			))

	def __get_index(self, date_start, date_end):
		photo_id, photo_votes, template_photos = None, [], []

		# Select all photos from the last snapshot before top date limit (approx.).
		top_photos = sorted(
			PhotoInfo.gql("WHERE date > :1 AND date < :2 ORDER BY date DESC", date_start, date_end + oneday).fetch(photos_upper_bound),
			key=lambda x: x.votes_count,
			reverse=True
		)

		if top_photos:
			# Take top 10 photo ids.
			top_photos = uniq([p.photo_id for p in top_photos])[:10]

			# Select voting data for top photos.
			infos = PhotoInfo.gql("WHERE photo_id IN :1 ORDER BY photo_id ASC, date ASC", top_photos)
			for info in infos:
				if date_start <= info.date.date() <= date_end:
					if photo_id and (photo_id != info.photo_id):
						# Commit next graph line when reached new photo id.
						self.__append_template_photo(template_photos, photo_id, photo_votes)
						photo_votes = []

					# Append data to current graph line.
					photo_votes.append(PhotoVote(info.date, int(mktime(info.date.timetuple()) / 60), info.votes_count))
					photo_id = info.photo_id

			# Commit last graph line.
			self.__append_template_photo(template_photos, photo_id, photo_votes)

		# Render page.
		html_template_values = {"photos": template_photos, "date_start": date_start, "date_end": date_end}
		json_template_values = {"photos": [Photo(photo.id, photo.votes[-20:]) for photo in template_photos if photo.id == 27 or photo.id == 28 or photo.id == 61]}
		path1 = os.path.join(os.path.dirname(__file__), "main.html")
		path2 = os.path.join(os.path.dirname(__file__), "graph.json")
		return template.render(path1, html_template_values), template.render(path2, json_template_values)

