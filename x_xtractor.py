import re
import os
import pickle
from helium import *
from time import sleep
from datetime import datetime, timedelta
from dateutil import parser
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import urllib.request
from ioc_finder import find_iocs


# Refactored function to start browser session and handle cookies
def start_browser_session(malware):
    try:
        browser = start_firefox(f"https://x.com/search?q={malware}&src=typed_query&f=live", headless=False)
        sleep(3)  # Allow time for the page to load
        
        #Checking if Cookies file exists or not
        if os.path.exists("cookies.pkl"):
            load_cookies(browser)
            go_to(f"https://x.com/search?q={malware}&src=typed_query&f=live")  # Refresh after loading cookies
            sleep(3)
        else:
            login_to_twitter(browser)
        return browser
    except Exception as e:
        print(f"Error starting browser session: {e}")
        return None

# Login if cookies do not exist. The user must enter login credentials in the terminal
def login_to_twitter(browser):
    username = input("Enter Username: ")
    password = input("Enter Password: ")
    try:
        write(username, into="Phone, email, or username")
        click('Next')
        wait_until(Text('Password').exists)
        write(password, into='Password')
        click('Log in')
        sleep(5)  # Allow time for login
        save_cookies(browser)
    except Exception as e:
        print(f"Login failed: {e}")

# Save cookies to a file for future use
def save_cookies(browser):
    try:
        with open("cookies.pkl", "wb") as file:
            pickle.dump(get_driver().get_cookies(), file)
    except Exception as e:
        print(f"Failed to save cookies: {e}")

# Load cookies from file if available
def load_cookies(browser):
    try:
        if os.path.exists("cookies.pkl"):
            with open("cookies.pkl", "rb") as file:
                cookies = pickle.load(file)
                for cookie in cookies:
                    get_driver().add_cookie(cookie)
    except Exception as e:
        print(f"Failed to load cookies: {e}")

# Parse and validate the timeframe input
def calculate_cutoff_time(timeframe):
    try:
        number, unit = timeframe.split()
        number = int(number)
        
        if unit in ['days', 'day', 'd']:
            return datetime.utcnow() - timedelta(days=number)
        elif unit in ['hours', 'hour', 'h']:
            return datetime.utcnow() - timedelta(hours=number)
        elif unit in ['weeks', 'week', 'w']:
            return datetime.utcnow() - timedelta(weeks=number)
        elif unit in ['months', 'month', 'm']:
            return datetime.utcnow() - timedelta(days=30 * number)
        elif unit in ['years', 'year', 'y']:
            return datetime.utcnow() - timedelta(days=365 * number)
        else:
            raise ValueError("Unsupported time unit")
    except ValueError as e:
        print(f"Invalid timeframe format: {e}")
        return None

# Check if a tweet timestamp is within the specified timeframe
def is_within_timeframe(tweet_time_str, cutoff_time):
    tweet_time = parser.isoparse(tweet_time_str).replace(tzinfo=None)
    return tweet_time >= cutoff_time

# Collect tweets based on the cutoff time
def collect_tweets(browser, cutoff_time):
    all_tweets = []
    scroll_attempts = 0

    while True:
        if scroll_attempts != 0:
            scroll_down(1000)
        sleep(3)
        
        tweets = find_all(S("//article[@role='article']"))
        
        if tweets:
            for tweet in tweets:
                tweet_text = tweet.web_element.text
                try:
                    time_element = tweet.web_element.find_element("tag name", "time")
                except NoSuchElementException:
                    print("Skipped tweet due to missing time info")
                    continue
                
                tweet_time = time_element.get_attribute("datetime")
                
                if not is_within_timeframe(tweet_time, cutoff_time):
                    print(f"Reached tweets older than {cutoff_time}, stopping...")
                    kill_browser()
                    return all_tweets
                
                all_tweets.append(tweet_text)
                print(f"Collected Tweet at {tweet_time}: {tweet_text}\n")
            
            scroll_attempts += 1
        else:
            print("No more tweets found, stopping...")
            break
    
    return all_tweets

# Save collected tweets to a text file
def save_collected_tweets(tweets):
    try:
        with open('collected_tweets.txt', 'w', encoding='utf-8') as file:
            for tweet in tweets:
                file.write(tweet + "\n")
    except IOError as e:
        print(f"Failed to save tweets: {e}")

# Extract and save IOCs from collected tweets, using ioc-finder module for it
def main_extractor(malware_name, cutoff_time):

    with open('collected_tweets.txt','r',encoding='utf-8') as file:
        tokens = re.split('\s+',file.read())

    output_data = {"urls":set(),
          "email_addresses":set(),
          "domains":set(),
          "ipv4s":set(),
          "md5s":set(),
          "sha1s":set(),
          "sha256s":set(),
          "sha512s":set(),
          "hashes":set()
          }
   
    ip_regex= r"((?:\d{1,3}(?:\[\.\]|\.|\[\.|\.\]|\(\.|\.\)|\(\.\)|\\\.|\/\.|\.\\|\.\/|dot|\[dot\]|\(dot\))?){3}\d{1,3})"
    ioc_types=["urls","email_addresses","domains","ipv4s","md5s","sha1s","sha256s","sha512s"]
    ip_defangers=["[.",".]","(.",".)","\\.",".\\","/.","./"]

    for token in tokens:
        if re.search(ip_regex, token):
            for ip_defanger in ip_defangers:
                if ip_defanger in token:
                    token = token.replace(ip_defanger,".")
        ioc_finder_result=find_iocs(token)
        hashes=ioc_finder_result["md5s"] + ioc_finder_result["sha1s"] + ioc_finder_result["sha256s"] + ioc_finder_result["sha512s"]
        for ioc_type in ioc_types:
            if ioc_finder_result[ioc_type]:
                if ioc_type == 'urls' and (ioc_finder_result["md5s"] or ioc_finder_result["sha1s"] or ioc_finder_result["sha256s"]or ioc_finder_result["sha512s"]):
                    output_data["hashes"].add(hashes[0])
                    break
                else:
                    output_data[ioc_type].add(ioc_finder_result[ioc_type][0])
                    break
    
    from_date = cutoff_time.date()
    today_date = datetime.now().date()
    malware_name =  "".join([malware_name[3:] if malware_name[:3] == "%23" else malware_name])
    malware_name = malware_name.split('%20')[0] if '%20' in malware_name else malware_name
    
    
    os.makedirs(malware_name, exist_ok=True)

    
    # Save as raw txt file
    output_file=os.path.join(malware_name,f"{malware_name}_{from_date}_to_{today_date}.txt")
    with open(output_file, 'w') as raw_file:
        #json.dump(output_data, json_file, indent=4)
        for key,iocs_list in output_data.items():
            for item in iocs_list:
                if key in ["domains","email_addresses","email_addresses_complete","ipv4s","urls","md5s","sha1s","sha256s","sha512s","hashes"]:
                    raw_file.write(item+"\n")
    
    print("Extracted IOCs saved to raw txt file:", output_data)



# Main function to start the process
def scrape_and_collect_tweets():
    try:
        malware = input("Enter the search query: ")
        malware=urllib.parse.quote(malware)
        malware = malware.lower()
        timeframe = input("Enter the timeframe (e.g., '7 days', '3 hours', '2 weeks'): ")
        cutoff_time = calculate_cutoff_time(timeframe)
        
        if not cutoff_time:
            print("Invalid timeframe, exiting...")
            return

        browser = start_browser_session(malware)
        
        if browser is None:
            print("Failed to start browser session.")
            return

        all_tweets = collect_tweets(browser, cutoff_time)
        save_collected_tweets(all_tweets)
        return malware, cutoff_time
    except Exception as e:
        print(f"Error encountered: {e}")

# Start the scraping and extraction process
malware_name, cutoff_time = scrape_and_collect_tweets()
if malware_name and cutoff_time:
    print("="*60)
    print("EXTRACTION STARTING: This may take 1 to 2 minutes .....")
    print("="*60)
    main_extractor(malware_name, cutoff_time)
