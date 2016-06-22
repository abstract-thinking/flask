import feedparser
import json
import urllib2
import urllib

from flask import Flask
from flask import render_template
from flask import request

app = Flask(__name__)

BBC_FEEDS = {'bbc': 'http://feeds.bbci.co.uk/news/rss.xml',
	     'cnn': 'http://rss.cnn.com/rss/edition.rss',
	     'fox': 'http://feeds.foxnews.com/foxnews/latest',
	     'iol': 'http://www.iol.co.za/cmlink/1.640' }

DEFAULTS = {'publication':'bbc',
	    'city':'London,UK' }

WHEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather={}&units=metric&appid={}'

@app.route("/")
def home():
	publication = request.args.get('publication')
	if not publication:
		publication = DEFAULTS['publication']
	articles = get_news(publication)

	with open('weather.txt', r+) as f:
		weather_api_key=f.read().splitlines()
	city = request.args.get('city')
	if not city:
		city = DEFAULTS['city']
	weather = get_weather(city, weather_api_key)
	return render_template("home.html",
		articles=feed['entries'],
		weather=weather)

def get_news(query):
	if not query or query.lower() not in RSS_FEEDS:
		publication = DEFAULTS['publication']
	else:
		publication = query.lower()
	feed = feedparser.parse(BBC_FEEDS[publication])
	return feed['entries']

def get_weather(query, weather_api_key): 
	query = urllib.quote(query)
	url = WHEATHER_URL.format(query, weather_api_key)
	data = urllib2.urlopen(url).read()
	parsed = json.loads(data)
	weather = None
	if parsed.get("weather"):
		weather = {"description" : parsed["weather"][0]["description"],
			"temperature" : parsed["main"]["temp"],
			"city" : parsed["name"],
			"country" : parsed["sys"]["country"]}
	return weather

if __name__ == '__main__':
	app.run(port=5000, debug=True)
