import datetime
import feedparser
import json
import os
import urllib2
import urllib

import logging

from flask import Flask
from flask import make_response
from flask import render_template
from flask import request

app = Flask(__name__)

RSS_FEEDS = {'bbc': 'http://feeds.bbci.co.uk/news/rss.xml',
	     'cnn': 'http://rss.cnn.com/rss/edition.rss',
	     'fox': 'http://feeds.foxnews.com/foxnews/latest',
	     'iol': 'http://www.iol.co.za/cmlink/1.640' }

DEFAULTS = {'publication':'bbc',
	    'city':'London,UK',
	    'currency_from':'GBP',
	    'currency_to':'USD' }

WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid={}"
CURRENCY_URL = "https://openexchangerates.org/api/latest.json?app_id={}"

def get_value_with_fallback(key):
	if request.args.get(key):
		return request.args.get(key)
	if request.cookies.get(key):
		return request.cookies.get(key)
	return DEFAULTS[key]

@app.route("/")
def home():
	api_keys = read_api_keys()

	publication = get_value_with_fallback('publication')
	articles = get_news(publication)

	city = get_value_with_fallback('city')
	weather = get_weather(city, api_keys['weather'])
	
	currency_from = get_value_with_fallback('currency_from')
	currency_to = get_value_with_fallback('currency_to')
	rate, currencies = get_rate(currency_from, currency_to, api_keys['currency'])
	
	response = make_response(render_template("home.html",
		articles=articles,
		weather=weather,
		currency_from=currency_from,
		currency_to=currency_to,
		rate=rate,
		currencies=sorted(currencies))
	
	expires = datetime.datetime.now() + datetime.timedelta(days=365)
	response.set_cookie("publication", publication, expires)
	response.set_cookie("city", city, expires=expires)
	response.set_cookie("currency_from", expires=expires)
	response.set_cookie("currency_to", currency_to, expires=expires)

	return response

def get_news(query):
	if not query or query.lower() not in RSS_FEEDS:
		publication = DEFAULTS['publication']
	else:
		publication = query.lower()
	feed = feedparser.parse(RSS_FEEDS[publication])
	return feed['entries']

def get_weather(query, weather_api_key): 
	query = urllib.quote(query)
	url = WEATHER_URL.format(query, weather_api_key)
	app.logger.info(url)
	data = urllib2.urlopen(url).read()
	parsed = json.loads(data)
	weather = None

	if parsed.get("weather"):
		weather = {"description" : parsed["weather"][0]["description"],
			"temperature" : parsed["main"]["temp"],
			"city" : parsed["name"],
			"country" : parsed["sys"]["country"]}
	return weather


def get_rate(frm, to, currency_api_key):
	all_currency = urllib2.urlopen(CURRENCY_URL.format(currency_api_key)).read()
	
	parsed = json.loads(all_currency).get('rates')
	frm_rate = parsed.get(frm.upper())
	to_rate = parsed.get(to.upper())
	return (to_rate/frm_rate, parsed.keys())

def read_api_keys():
	script_dir = os.path.dirname(__file__)	
	abs_file_path = os.path.join(script_dir, "weather.txt")
	d = {}
	with open(abs_file_path) as f:
		for line in f:
			(key, val) = line.split()
			d[key] = val.strip()
	return d

if __name__ == '__main__':
	app.run(port=5000, debug=True)
