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

---
## Usage
- Download the two scripts and store them into a new folder
- Run the x_xtractor first.
- Then in the input fields give the name of the malware without any spaces use camelCase for multi word malware name or url encode the query if you have to use space or any special characters.
- In the next filed you will be asked for time frame to extract the tweets. Enter the time frame in the following format => e.g.,'1 days', '7 days', '3 hours', '2 weeks', '2 months','2 years'.
- If you are using the script for first time you will not have `cookie.pkl` file which will contain the session cookie for the X account. (The session cookie is stored for later uses because logging in multiple times may cause X to flag your account for suspicious activity). Since you wont have `cookie.pkl` file you will be asked for your username and password in the terminal itself for the first login.
- Then the firefox web driver will launch and start scraping the tweets and store the collected tweets in `collected_tweets.txt` file.
- After completion of collection of tweet, iocs from the tweets are extracted. It mainly collects IPs and Hashes. It can also collect domains as well but is not printed by default (we use regex to extract the domains so regex is picking up the file names, legit domains, .... and other garbage as well).
