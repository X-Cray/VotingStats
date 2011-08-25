from datetime import date
from time import strptime

date_formats_with_year = ["%d %m %Y", "%Y %m %d", "%d %B %Y", "%B %d %Y", "%d %b %Y", "%b %d %Y", "%d %m %y", "%y %m %d", "%d %B %y", "%B %d %y", "%d %b %y", "%b %d %y"]
date_formats_without_year = ["%d %B", "%B %d", "%d %b", "%b %d"]

def uniq(alist):
	set = {}
	return [set.setdefault(e, e) for e in alist if e not in set]

def parse_date(string):
	string = string.strip()

	if not string:
		return None

	string = string.replace("/", " ").replace("-", " ").replace(",", " ")

	for format in date_formats_with_year:
		try:
			result = strptime(string, format)
			return date(result.tm_year, result.tm_mon, result.tm_mday)
		except ValueError:
			pass

	for format in date_formats_without_year:
		try:
			result = strptime(string, format)
			year = date.today().year
			return date(year, result.tm_mon, result.tm_mday)
		except ValueError:
			pass

	raise ValueError()
