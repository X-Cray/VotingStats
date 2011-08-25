import os
import re
import logging
from google.appengine.ext.webapp import template
from common import *
from proxy import *

# More precise address regex.
proxy_address_regex = re.compile("(([\w\-]+\.)+\w+)\s*:\s*(\d+)")

class ManualGrabber(ProxyBase):
	def get(self):
		path = os.path.join(os.path.dirname(__file__), "proxy-add-form.html")
		self.response.out.write(template.render(path, None))

	def post(self):
		proxies = self.request.get("proxies")

		if proxies:
			proxy_type = "http"
	
			if proxies.startswith("socks4"):
				proxy_type = "socks4"
			elif proxies.startswith("socks5"):
				proxy_type = "socks5"

			proxies_list = proxy_address_regex.findall(proxies)
			if proxies_list:
				for proxy in proxies_list:
					proxy_address = "%s:%s" % (proxy[0], proxy[2])
					if not self.proxies_contain_key(proxy_address):
						self.save_proxy(proxy_address, proxy_type, None)

		self.get()