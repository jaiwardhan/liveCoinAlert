#LiveCoinAlert

Standalone python program to continously monitor cryptocurrency market and coins of your choice. Uses <a hreaf="https://coinmarketcap.com/"><b>CoinmarketCap</b></a> public API to fetch live data from the ticker. While make any changes to your version of this tool, please ensure your rest call queries are limited to the threshold limitations as specified by coinmarketcap.


##Usage
Use the AlerConfiguration.json to specify the coins you want to monitor from coinmarketcap ticker. A sample usage has been mentioned in the json itself, you can customize your way. Also this json configuration is always loaded in every call, so you can directly open an editor to specify new coins, high/low limits and volume controls and directly save it. A special night mode has been added just incase you want the volume and alert levels to be different during the night time. Also if you are in a different time zone other than India, just change the time offset in the configuration json and save it - There is absolutely no necessity to stop the script at that point of time.

##Running
Using python 2.7, directly headover to the repo folder and run it with python:

(jazz@jaisMacBookPro) (master)* $  python coinalert.py


##Upcoming
Feel free to cut out a branch from the master and add any additional features you want send me the pull request. Helpful features and tools will be seriously cool integrate. In the upcoming versions, I will try to integrate fibbonacci analysis of coins and then decide wether its a good point to enter the market, or if the market sentiments seems to negative. Other suggestions are welcome as well.


Special mention to <a href="https://bitcoincharts.com" target="_blank">Bitcoincharts</a> for their API.
Excellent realtime historical data (second by second) can be found <a href="http://api.bitcoincharts.com/v1/trades.csv?symbol=bitstampUSD&start=1501416543">here</a>.

Ping me:
Telegram: @jaiwardhan_live
Twitter: @jaiwardhan_live

Donate to help me add paid apis to this tool:
BTC: 19HWYGvA7xUizmYAmC5pa58RosM3Rqmmxh
LTC: LYT7URhvaYfFKPEwYLBivzozpFku6Leb2r
