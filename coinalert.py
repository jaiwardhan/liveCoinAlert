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
Module to load configuration and runtime params directly
from a config. This may allow us to modify the runtime params
on the fly without having to stop the program. This also helps
us since we wouldn't stop the program in the future if it
has critical built up data from past days (since we are not using
a local or a firebase storage as of now)
'''
class ConfigurationManager:
	configURL = "./alertConfiguration.json"
	configData = ""
	def load(self):
		self.configData = json.load(open(self.configURL))


	def getConfig(self):
		self.load()
		return self.configData


'''
Submodule to send out alerts on the mac system
'''
class Alerter:

	# convert gmt hour to ist by adding offset 
	# for hours
	def toLocalTime(self, gmHour, configuration):
		totTime = 24 + int(configuration["timeZoneHour"])	#since it can be -ve and modulus of -ve is not same as +ve numbers
		return (gmHour + totTime)%24

	# Decides if it is night time or not
	def isNightTime(self, hour):
		if hour <= 7 and hour > 0:
			return True
		return False

	# Method to send out an alert from the mac osx
	# system. Currently not checking system configuration.
	# Controls volume based on the time and alerts based
	# on the configuration passed.
	def doAlert(self, message, mode, configuration):

		gmHourNow = strftime("%H", gmtime())
		localHour = self.toLocalTime(int(gmHourNow), configuration)
		isItNight = self.isNightTime(localHour)

		#osascript subcommand string
		volcontroller = 'set volume output volume '

		#fill in the volumae based on the current conditions from
		# the passed configuration
		if isItNight == True:
			if mode == 'ALERT':
				volcontroller = volcontroller + str(configuration["volume"]["nightmode"]["alert"])
			else:
				volcontroller = volcontroller + str(configuration["volume"]["nightmode"]["default"])
		else:
			if mode == 'ALERT':
				volcontroller = volcontroller + str(configuration["volume"]["daymode"]["alert"])
			else:
				volcontroller = volcontroller + str(configuration["volume"]["daymode"]["default"])

		#Control the volume accordingly by running the script
		os.system("osascript -e \'"+volcontroller+"\'")

		#configure bot options picked from the config
		botOptions = ""
		for eachBotOption in configuration["bot_options"]:
			botOptions = botOptions + configuration["bot_options"][eachBotOption] + " "

		#say the message - osx internals used
		os.system('Say '+botOptions +message)

'''
Submodule to check subscriptions and send notifs if required.
'''
class NotifSubscriptions:

	subsAlert = ''

	coinsToMonitor 		= []
	coinsPriceData 		= [] #USD
	coinsTrendForNotif 	= []

	# Loader
	def load(self):
		self.subsAlert = Alerter()

	# Simple comparator to check if a > b
	def compareMore(self, arg1, arg2):
		if float(arg1) > float(arg2):
			return True
		return False

	# Simple comparator to check if a < b
	def compareLess(self, arg1, arg2):
		if float(arg1) < float(arg2):
			return True
		return False

	# Load configuration from all the data in the
	# config parameter and flushing the older one
	def loadConfiguration(self, configuration):
		try:
			# first flush all
			self.coinsToMonitor 		= []
			self.coinsPriceData 		= []
			self.coinsTrendForNotif 	= []

			#start pushing configuration data
			for keys in configuration["alerts"]:
				self.coinsToMonitor.append(configuration["alerts"][keys]["symbol"])
				self.coinsPriceData.append(configuration["alerts"][keys]["price"])
				self.coinsTrendForNotif.append(configuration["alerts"][keys]["band"])
		except:
			print "Problem encountered while refreshing alert data: f(loadConfiguration)"

	# Check if the coin price and trend matches with some
	# alert that is mentioned in the coins to monitor. If
	# it does, generate an alert and send out a notification.
	def check(self, coinSymbol, coinPrice, coinTrend, configuration):
		iterator = 0
		#refresh the configuration
		self.loadConfiguration(configuration)

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
						self.subsAlert.doAlert(message, "ALERT", configuration)
			iterator = iterator + 1


class CoinAlert:

	#the runtime configuration
	config = ''

	coinTickerAlerts = ""

	coinsToMonitor = []		# To be picked from the config
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
		try:
			maxAllowedRank = int(self.config["runtime_params"]["topAssetsMaxRank"])
			if int(assetRank) <= maxAllowedRank and int(assetRank) > 0:
				return True
			return False
		except:
			print "Error calculating in f(isAmongstTopAsset)"

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
			# Load the fresh config
			self.loadConfiguration()
			# Reload coin config
			self.loadCoins()

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
								self.notificationCenter.check(symbol, tickerObj[eachIdx]['price_usd'], 'MORE', self.config)
							elif str(alert) == str(self.DROP_SIGNAL):
								self.notificationCenter.check(symbol, tickerObj[eachIdx]['price_usd'], 'LESS', self.config)

							#check extra data
							if currentPercentageChange < 0.0:
								alert = alert + self.EXTRA_DATA_DROP
							elif currentPercentageChange > 0.0:
								alert = alert + self.EXTRA_DATA_RISE
							else:
								alert = alert + self.EXTRA_DATA_FLAT


							if currentPercentageChange > 1.0 and currentPercentageChange > (self.lastPriceChanged[symbolIndex] + 1.0) :
								self.coinTickerAlerts.doAlert(' Price increased.', 'NORMAL', self.config)
								pincreased = 1
								self.lastPriceChanged[symbolIndex] = currentPercentageChange
								alert = self.ALERT_SIGNAL + alert
							elif currentPercentageChange < (self.lastPriceChanged[symbolIndex] - 1.0):
								self.coinTickerAlerts.doAlert(' Price dropped.', 'NORMAL', self.config)
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
						threshold = int(self.config["runtime_params"]["topAssetsFilterThreshold"])
						topTotalLimit = int(self.config["runtime_params"]["topAssetsMaxRank"])
						topIdx = 0
						header = "\n.: top "+str(threshold)+" GAINERS (% 24hrs, top "+str(topTotalLimit)+" ) :."
						
						if len(topRankers) >= 2*threshold:
							header = header + "\t" +"  .: top "+str(threshold)+" Losers (% 24hrs, top "+str(topTotalLimit)+" ) :."

						print header


						while topIdx < len(topRankers) and topIdx < threshold :
							toppers = topRankers[topIdx]["symbol"]+" "+topRankers[topIdx]["name"]+"  \t==> "+str(topRankers[topIdx][self.getDeltaCode(DAY_ONE)])
							losers = ""

							if len(topRankers) >= 2*threshold:
								losers = topRankers[len(topRankers) -1 -topIdx]["symbol"]+" "+topRankers[len(topRankers) -1 -topIdx]["name"]+"   \t==> "+str(topRankers[len(topRankers) -1 -topIdx][self.getDeltaCode(DAY_ONE)])
							print toppers + "\t\t\t" +losers
							topIdx = topIdx + 1


			except:
				print "Ignore Exception"

			print ""
			sleep(7)



	#Method load runtime configuration from the config
	def loadConfiguration(self):
		self.config = ConfigurationManager().getConfig()

	# Coins loader
	def loadCoins(self):
		self.loadConfiguration()
		coinsFromConfig = self.config["runtime_params"]["coinsToMonitor"]

		# Check for any additional coins mentioned
		# in the config but are not in the program memory.
		# If an entry is new in the config, then append one.
		for eachCoinSymbol in coinsFromConfig:
			if not eachCoinSymbol in self.coinsToMonitor:
				# then append one in the list
				self.coinsToMonitor.append(eachCoinSymbol)
				# add their respective history inits
				self.lastPriceChanged.append(0.0)
				self.liveData.append(0.0)


		# Reverse check: Check wether an entry has now been
		# removed from the config. If it is and it is still
		# present in the program memory, then remove it.
		for eachCoinSymbol in self.coinsToMonitor:
			if not eachCoinSymbol in coinsFromConfig:
				# get the current index to splice
				currentIndex = self.coinsToMonitor.index(eachCoinSymbol)

				if currentIndex >= 0 :
					#splice and reappend the list from here
					self.coinsToMonitor = self.coinsToMonitor[:currentIndex] + self.coinsToMonitor[currentIndex +1: ]
					self.lastPriceChanged = self.lastPriceChanged[:currentIndex] + self.lastPriceChanged[currentIndex +1:]
					self.liveData = self.liveData[:currentIndex] + self.liveData[currentIndex+1:]

	# Class loader
	def load(self, delta):
		# Check for delta being reffered for
		if self.deltaTime != delta:
			self.deltaTime = delta

		# Load coins data
		self.loadCoins()
		eachIdx = 0
		while eachIdx < len(self.coinsToMonitor):
			self.lastPriceChanged.append(0.0)
			self.liveData.append(0.0)
			eachIdx = eachIdx + 1
		self.notificationCenter = NotifSubscriptions()
		self.notificationCenter.load()
		self.coinTickerAlerts = Alerter()

coinAlert = CoinAlert()
coinAlert.load(MINUTE_ONE)
coinAlert.start()
