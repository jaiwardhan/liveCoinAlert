import requests
import json
import matplotlib.pyplot as plt
from forex_python.converter import CurrencyRates
from time import *
import os


MINUTE_ONE = 1
DAY_ONE = 24
DAY_SEVEN = 7

'''
Submodule to send out alerts on the mac system
'''
class Alerter:

	def toIST(self, gmHour):
		return (gmHour + 5)%24

	def isNightTime(self, hour):
		if hour <= 7 and hour > 0:
			return True

		return False

	def doAlert(self, message, mode):
		gmHourNow = strftime("%H", gmtime())
		istHour = self.toIST(int(gmHourNow))
		isItNight = self.isNightTime(istHour)
		if isItNight == True:
			# Set system volume for emergencies as 40 and 20 as normal
			if mode == 'ALERT':
				os.system("osascript -e 'set volume output volume 15'")
			else:
				os.system("osascript -e 'set volume output volume 10'")
		else:
			# set sysmte volume for emergencies as 80 and 60 as normal
			if mode == 'ALERT':
				os.system("osascript -e 'set volume output volume 60'")
			else:
				os.system("osascript -e 'set volume output volume 40'")

		os.system('Say -v Daniel '+message)

'''
Submodule to check subscriptions and send notifs if required.
'''
class NotifSubscriptions:

	subsAlert = ''

	coinsToMonitor 		= ['BTC', 	'BTC']
	coinsPriceData 		= ['2850', 	'2400'] #USD
	coinsTrendForNotif 	= ['MORE',	'LESS']
	comparatorFunction = ''

	def load(self):
		self.subsAlert = Alerter()

	def compareMore(self, arg1, arg2):
		if float(arg1) > float(arg2):
			return True
		return False

	def compareLess(self, arg1, arg2):
		if float(arg1) < float(arg2):
			return True
		return False


	coinsNotifComparator = {
		'MORE' 	: compareMore,
		'LESS'	: compareLess
	}

	def createAlert(self, message, reps):
		eachRep = 0
		while eachRep < reps:
			os.system('Say '+message)
			eachRep = eachRep + 1

	def check(self, coinSymbol, coinPrice, coinTrend):
		iterator = 0
		while iterator < len(self.coinsToMonitor):
			if coinSymbol == self.coinsToMonitor[iterator]:
				if coinTrend == self.coinsTrendForNotif[iterator] :
					result = False
				
					if coinTrend == 'MORE':
						result = str(self.compareMore(float(coinPrice), float(self.coinsPriceData[iterator])))
					elif coinTrend == 'LESS':
						result = str(self.compareLess(float(coinPrice), float(self.coinsPriceData[iterator])))

					if str(result) == 'True':
						message = " Alert! alert! alert! Price of "+ coinSymbol + " went "+coinTrend+" than threshold of "+str(self.coinsPriceData[iterator])
						self.subsAlert.doAlert(message, "ALERT")
			iterator = iterator + 1


class CoinAlert:

	coinTickerAlerts = ""

	coinsToMonitor = ['BTC', 'LTC', 'GNT', 'ETH', 'DASH', 'XRP', 'XMR', 'ANT', 'REP', 'DCR', 'EOS', 'GNO']
	deltaTime = MINUTE_ONE
	tickerURL = 'https://api.coinmarketcap.com/v1/ticker/'
	deltaCoinPerChange = 1.0
	lastPriceChanged = []
	liveData = []

	topAssets = []
	TOP_ASSETS_MAX_RANK = 15	#Set the max top ranking assets you want to see
	TOP_ASSETS_FILTER_THRESHOLD = 5	#set this to the top ones which you want to see in the additional data

	DROP_SIGNAL = "[ \/ ]"
	RISE_SIGNAL = "[ /\\ ]"
	FLAT_SIGNAL = "[ -- ]"
	SPACER_SIGNAL = " \t   "
	ALERT_SIGNAL = " \t X "
	EXTRA_DATA_RISE = "[RISE]"
	EXTRA_DATA_DROP = "[DROP]"
	EXTRA_DATA_FLAT = "[FLAT]"

	notificationCenter = ''

	def load(self, delta):
		if self.deltaTime != delta:
			self.deltaTime = delta
		eachIdx = 0
		while eachIdx < len(self.coinsToMonitor):
			self.lastPriceChanged.append(0.0)
			self.liveData.append(0.0)
			eachIdx = eachIdx + 1
		self.notificationCenter = NotifSubscriptions()
		self.notificationCenter.load()
		self.coinTickerAlerts = Alerter()

	def requestGet(self, url):
		print "requesting url: "+url
		response = requests.get(url)
		return response

	def getDeltaCode(self, delta):
		if delta == MINUTE_ONE:
			return "percent_change_1h"
		elif delta == DAY_ONE:
			return "percent_change_24h"
		elif delta == DAY_SEVEN:
			return "percent_change_7d"
		return "percent_change_1h"

	def getTickerIndex(self, symbol):
		eachIdx = 0
		while eachIdx < len(self.coinsToMonitor):
			if self.coinsToMonitor[eachIdx] == symbol:
				return eachIdx
			eachIdx = eachIdx + 1
		return -1

	def isAmongstTopAsset(self, assetRank):
		if int(assetRank) <= self.TOP_ASSETS_MAX_RANK and int(assetRank) > 0:
			return True
		return False

	def getAssetRankFromObject(self, assetObject):
		return assetObject["rank"]

	def customSortTopAssets(self, a, b):
		if float(a["percent_change_24h"]) > float(b["percent_change_24h"]):
			return -1
		elif float(a["percent_change_24h"]) == float(b["percent_change_24h"]):
			return 0
		return 1

	def start(self):
		while True:
			self.results = []
			try:
				response = self.requestGet(self.tickerURL)
				tickerObj = json.loads(response.text)
				
				if type(tickerObj) is dict:
					print "Unknown data"
					return
				else:
					eachIdx = 0
					print str(len(tickerObj))
					topRankers = []
					while eachIdx < len(tickerObj):
						#check if this asset is in the top ones to monitor
						if self.isAmongstTopAsset(self.getAssetRankFromObject(tickerObj[eachIdx])):
							#then push this to top rankers index
							topRankers.append(tickerObj[eachIdx])

						if tickerObj[eachIdx]['symbol'] in self.coinsToMonitor:
							symbol = tickerObj[eachIdx]['symbol']
							timeStamp = "percent_change_1h"

							if self.deltaTime == MINUTE_ONE:
								timeStamp = self.getDeltaCode(MINUTE_ONE)
							elif self.deltaTime == DAY_ONE:
								timeStamp = self.getDeltaCode(DAY_ONE)
							elif self.deltaTime == DAY_SEVEN:
								timeStamp = self.getDeltaCode(DAY_SEVEN)

							currentPercentageChange = float(tickerObj[eachIdx][timeStamp])
							symbolIndex = self.getTickerIndex(symbol)
							pincreased = 0
							alert = ""

							#check if this is a live increase or decrease
							if currentPercentageChange > self.liveData[symbolIndex]:
								alert = self.RISE_SIGNAL
							elif currentPercentageChange < self.liveData[symbolIndex]:
								alert = self.DROP_SIGNAL
							else:
								alert = self.FLAT_SIGNAL

							# Check threshold alerts
							if str(alert) == str(self.RISE_SIGNAL):
								self.notificationCenter.check(symbol, tickerObj[eachIdx]['price_usd'], 'MORE')
							elif str(alert) == str(self.DROP_SIGNAL):
								self.notificationCenter.check(symbol, tickerObj[eachIdx]['price_usd'], 'LESS')

							#check extra data
							if currentPercentageChange < 0.0:
								alert = alert + self.EXTRA_DATA_DROP
							elif currentPercentageChange > 0.0:
								alert = alert + self.EXTRA_DATA_RISE
							else:
								alert = alert + self.EXTRA_DATA_FLAT


							if currentPercentageChange > 1.0 and currentPercentageChange > (self.lastPriceChanged[symbolIndex] + 1.0) :
								self.coinTickerAlerts.doAlert(' Price increased.', 'NORMAL')
								pincreased = 1
								self.lastPriceChanged[symbolIndex] = currentPercentageChange
								alert = self.ALERT_SIGNAL + alert
							elif currentPercentageChange < (self.lastPriceChanged[symbolIndex] - 1.0):
								self.coinTickerAlerts.doAlert(' Price dropped.', 'NORMAL')
								pincreased = -1
								self.lastPriceChanged[symbolIndex] = currentPercentageChange
								alert = self.ALERT_SIGNAL + alert
							else:
								alert = self.SPACER_SIGNAL + alert
							status = symbol + " " +str(tickerObj[eachIdx]["name"])
							status = status + alert
							print status + " USD: $"+str(tickerObj[eachIdx]["price_usd"])+"\t==> 1hr %age: "+str(currentPercentageChange) + ", 24hr %age: "+str(tickerObj[eachIdx]["percent_change_24h"])
						eachIdx = eachIdx + 1

					#sort the toppers for gainers list
					if len(topRankers) > 0:
						topRankers.sort(self.customSortTopAssets)
						#print the top X assets
						topIdx = 0
						print "\n::TOP GAINERS (% 24hrs) ::"
						while topIdx < len(topRankers) and topIdx < self.TOP_ASSETS_FILTER_THRESHOLD:
							print topRankers[topIdx]["symbol"]+"\t"+topRankers[topIdx]["name"]+" ==>\t"+str(topRankers[topIdx][self.getDeltaCode(DAY_ONE)])
							topIdx = topIdx + 1


			except:
				print "Ignore Exception"

			print ""
			sleep(7)

coinAlert = CoinAlert()
coinAlert.load(MINUTE_ONE)
coinAlert.start()
