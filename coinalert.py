import requests
import json
import matplotlib.pyplot as plt
from forex_python.converter import CurrencyRates
import time
import os


MINUTE_ONE = 1
DAY_ONE = 24
DAY_SEVEN = 7

class CoinAlert:

	coinsToMonitor = ['BTC', 'LTC', 'GNT', 'ETH', 'DASH', 'XRP', 'XMR', 'ANT', 'REP', 'DCR', 'EOS']
	deltaTime = MINUTE_ONE
	tickerURL = 'https://api.coinmarketcap.com/v1/ticker/'
	deltaCoinPerChange = 1.0
	lastPriceChanged = []
	liveData = []

	DROP_SIGNAL = "[ \/ ]"
	RISE_SIGNAL = "[ /\\ ]"
	FLAT_SIGNAL = "[ -- ]"
	SPACER_SIGNAL = " \t   "
	ALERT_SIGNAL = " \t X "
	EXTRA_DATA_RISE = "[RISE]"
	EXTRA_DATA_DROP = "[DROP]"
	EXTRA_DATA_FLAT = "[FLAT]"

	def load(self, delta):
		if self.deltaTime != delta:
			self.deltaTime = delta
		eachIdx = 0
		while eachIdx < len(self.coinsToMonitor):
			self.lastPriceChanged.append(0.0)
			self.liveData.append(0.0)
			eachIdx = eachIdx + 1

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

					while eachIdx < len(tickerObj):
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

							#check extra data
							if currentPercentageChange < 0.0:
								alert = alert + self.EXTRA_DATA_DROP
							elif currentPercentageChange > 0.0:
								alert = alert + self.EXTRA_DATA_RISE
							else:
								alert = alert + self.EXTRA_DATA_FLAT



							if currentPercentageChange > 1.0 and currentPercentageChange > (self.lastPriceChanged[symbolIndex] + 1.0) :
								os.system('Say -v Daniel price increased. ')
								pincreased = 1
								self.lastPriceChanged[symbolIndex] = currentPercentageChange
								alert = self.ALERT_SIGNAL + alert
							elif currentPercentageChange < (self.lastPriceChanged[symbolIndex] - 1.0):
								os.system('Say -v Daniel price dropped. ')
								pincreased = -1
								self.lastPriceChanged[symbolIndex] = currentPercentageChange
								alert = self.ALERT_SIGNAL + alert
							else:
								alert = self.SPACER_SIGNAL + alert
							status = symbol + " " +str(tickerObj[eachIdx]["name"])
							# if pincreased == -1:
							# 	status = status + " \t[ \/ ]"
							# elif pincreased == 1:
							# 	status = status + " \t[ /\\ ]"
							# else:
							# 	status = status + " \t[ -- ]"
							status = status + alert
							print status + " USD: $"+str(tickerObj[eachIdx]["price_usd"])+"\t==> 1hr %age: "+str(currentPercentageChange) + ", 24hr %age: "+str(tickerObj[eachIdx]["percent_change_24h"])
						eachIdx = eachIdx + 1
			except:
				print "Ignore Exception"

			print ""
			time.sleep(7)

coinAlert = CoinAlert()
coinAlert.load(MINUTE_ONE)
coinAlert.start()
