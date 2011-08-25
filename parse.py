import re
from urllib import FancyURLopener
from google.appengine.api.taskqueue import Task
from google.appengine.ext import webapp
from google.appengine.ext import db
from common import *
from data import *

votes_count_regex = re.compile("<br><b><span title=\".+\">(\d+)</span></b><br>")
photo_page_template = "http://lavina.dp.ua/fotoConcurs.php?pid=%d"

class PageParser(webapp.RequestHandler):
	def post(self):
		photo_id = int(self.request.get("photo_id"))
		pageBody = self.__load_photo_page(photo_id)
		votes_count = self.__get_votes_count(pageBody)

		if votes_count is not None:
			self.__save_result(photo_id, votes_count)

		#print "Photo %s votes count is %s" % (photo_id, votes_count)

	def __get_votes_count(self, body):
		votes_count = votes_count_regex.search(body)
		return votes_count and int(votes_count.group(1))

	def __load_photo_page(self, photo_id):
		opener = FancyURLopener()
		res = None
		body = None
		link = photo_page_template % photo_id

		try:
			res = opener.open(link)
			body = res.read()
		except IOError, error:
			print "[!] {0}".format(error.strerror)
		finally:
			res and res.close()

		return body

	def __save_result(self, photo_id, votes_count):
		db.run_in_transaction(self.__save_result_internal, photo_id, votes_count)

	def __save_result_internal(self, photo_id, votes_count):
		PhotoInfo(photo_id=photo_id, votes_count=votes_count).put()

class ParseArranger(webapp.RequestHandler):
	def get(self):
		for photo_id in range(1, photos_upper_bound):
			task = Task(url="/parse-page", params={"photo_id": photo_id})
			task.add("parse")
