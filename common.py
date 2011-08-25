from datetime import timedelta

photos_upper_bound = 300
oneday = timedelta(1)
onehour = timedelta(0, 0, 0, 0, 0, 1)
onemonth = timedelta(20)
halfhour = timedelta(0, 0, 0, 0, 31)

cache_permanent_time = 0
cache_index_time = 40 * 60 # 40 minutes
cache_index_key = "index-page"
cache_data_key_template = "%s-data"
cache_votes_log_key = "votes-log"
cache_vote_arrangements_log_key = "vote-arrangements-log"
cache_proxies_log_key = "proxies-log"
cache_grabber_misses = "grabber_misses"
cache_grabber_status = "grabber_status"
cache_grabber_wakeup = "grabber_wakeup"
