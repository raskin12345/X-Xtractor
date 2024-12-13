# X-Xtractor
---

- This used to extract tweets from `https://x.com/search?q=<malware_name>&src=typed_query&f=live` url. This url is used to search the malware like `remcos`, `lumma`, etc. in X's search qurey's latest tab. Doing so will give us the latest IOCs shared by community using that malware name in the tweet.
- The `x_xtractror.py` now scrapes twitter and extract iocs as well.
---
## Requirements

```
pip install helium
```

```
pip install pickle
```

```
pip install python-dateutil
```

```
pip install ioc-finder
```

---
## Usage
- Download the two scripts and store them into a new folder
- Run the x_xtractor first.
- Then in the input fields give the name of the malware when it asks for search query.
- In the next filed you will be asked for time frame to extract the tweets. Enter the time frame in the following format => e.g.,'1 days', '7 days', '3 hours', '2 weeks', '2 months','2 years'.
- If you are using the script for first time you will not have `cookie.pkl` file which will contain the session cookie for the X account. (The session cookie is stored for later uses because logging in multiple times may cause X to flag your account for suspicious activity). Since you wont have `cookie.pkl` file you will be asked for your username and password in the terminal itself for the first login.
- Then the firefox web driver will launch and start scraping the tweets and store the collected tweets in `collected_tweets.txt` file.
- After completion of collection of tweet, iocs from the tweets are extracted. The extracted iocs are urls, domains, email addresses, hashes, ipv4s. There is high rate of false positive if you include urls and domains. The extracted iocs will be stored in a file inside a subdirectory that lies in the same directory as the script (also the subdirectory name and ioc file name is based on the search query and time).
