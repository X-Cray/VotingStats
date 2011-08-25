import urllib
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from grab_1 import *
from grab_2 import *
from grab_manual import *
from vote import *
from parse import *
from main import *
from api import *
from clean import *

urllib.getproxies_macosx_sysconf = lambda: {} # Hack for OSX.

application = webapp.WSGIApplication([
	("/", MainPage),
	("/parse", ParseArranger),
	("/parse-page", PageParser),
	("/grab1", Insorg1Grabber),
	("/grab2", Insorg2Grabber),
	("/grab-manual", ManualGrabber),
	("/vote", VoteArranger),
	("/clean", DataCleaner),
	("/vote-photo", Voter),
	("/api/settings", SettingsManager),
	("/api/status", StatusViewer),
	("/api/graph", GraphViewer)
], debug=True)

def real_main():
	run_wsgi_app(application)

def profile_main():
	# This is the main function for profiling
	# We've renamed our original main() above to real_main()
	import cProfile, pstats
	prof = cProfile.Profile()
	prof = prof.runctx("real_main()", globals(), locals())
	print "<pre>"
	stats = pstats.Stats(prof)
	stats.sort_stats("time") # Or cumulative
	stats.print_stats(80)  # 80 = how many to print
	# The rest is optional.
	# stats.print_callees()
	# stats.print_callers()
	print "</pre>"

main = real_main

if __name__ == "__main__":
	main()
