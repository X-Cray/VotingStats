import logging
from datetime import datetime
from google.appengine.ext import webapp
from google.appengine.ext import db
from common import *
from data import *

cleanup_max_entities = 500

class DataCleaner(webapp.RequestHandler):
	def get(self):
		objects = PhotoInfo.gql("WHERE date < :1", datetime.now() - onemonth).fetch(cleanup_max_entities)
		logging.info("Deleting %d expired objects" % len(objects))
		self.__delete_objects(objects)

	def __delete_objects(self, objects):
		for object in objects:
			logging.info("Deleting object from: %s" % object.date)
			db.run_in_transaction(self.__delete_object_internal, object)

	def __delete_object_internal(self, object):
		object.delete()
