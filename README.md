# X-Xtractor
- The `time_x_ioc.py` is used to extract tweets from `https://x.com/search?q=%23<malware_name>&src=typed_query&f=live` url. This url is used to search the malware with the hash tags like `#remcos`, `#lumma`, etc. in X's search qurey's latest tab. Doing so will give us the latest IOCs shared by community using `#<malware_name>` hashtag in their tweet.
- The `extractor.py` is simply used to extract the IOCs (currently only IPs and hashes) from the tweets collected in the `collected_tweets.txt` text file.
