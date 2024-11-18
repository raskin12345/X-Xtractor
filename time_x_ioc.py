import pickle
import os
from time import sleep
from datetime import datetime, timedelta
from dateutil import parser
from selenium.common.exceptions import NoSuchElementException
from helium import start_firefox, write, click, go_to, kill_browser, wait_until, find_all, S

from extractor import main_extractor

# Function to save cookies to a file
def save_cookies(browser):
    with open("cookies.pkl", "wb") as file:
        pickle.dump(browser.get_cookies(), file)

# Function to load cookies from a file
def load_cookies(browser):
    if os.path.exists("cookies.pkl"):
        with open("cookies.pkl", "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                browser.add_cookie(cookie)

# Function to calculate the cutoff time based on the user-defined timeframe
def calculate_cutoff_time(timeframe):
    number, unit = timeframe.split()
    number = int(number)

    # Calculate the timedelta based on the unit (e.g., days, hours, weeks, months, years)
    time_units = {
        'd': timedelta(days=number),
        'h': timedelta(hours=number),
        'w': timedelta(weeks=number),
        'm': timedelta(days=30 * number),  # Approximate 30 days per month
        'y': timedelta(days=365 * number)  # Approximate 365 days per year
    }

    unit = unit[0]  # Normalize to first character (e.g., 'day' -> 'd')

    if unit in time_units:
        return datetime.utcnow() - time_units[unit]
    else:
        raise ValueError("Unsupported time unit")

# Function to check if a tweet is within the specified timeframe
def is_within_timeframe(tweet_time_str, cutoff_time):
    tweet_time = parser.isoparse(tweet_time_str).replace(tzinfo=None)  # Convert to offset-naive datetime object
    return tweet_time >= cutoff_time

# Function to log in to Twitter (X) and save cookies
def login_to_twitter(browser, username, password):
    write(username, into="Phone, email, or username")
    click('Next')
    wait_until(lambda: 'Password' in find_all("Text"))
    write(password, into='Password')
    click('Log in')
    sleep(5)  # Wait for login to complete
    save_cookies(browser)  # Save cookies for future use

# Function to scrape and collect tweets based on hashtag and timeframe
def scrape_and_collect_tweets():
    malware = input("Enter the hashtag to search for: ")
    timeframe = input("Enter the timeframe (e.g., '7 days', '3 hours', '2 weeks'): ")

    # Calculate the cutoff time based on the user input
    cutoff_time = calculate_cutoff_time(timeframe)
    print(f"Scraping tweets from the last {timeframe}, cutoff time: {cutoff_time}")

    # Start the browser and navigate to Twitter (X) search page
    browser = start_firefox(f"https://x.com/search?q=%23{malware}&src=typed_query&f=live", headless=False)
    sleep(3)  # Wait for the page to load

    # Check if cookies exist and load them to bypass login
    if os.path.exists("cookies.pkl"):
        load_cookies(browser)
        go_to(f"https://x.com/search?q=%23{malware}&src=typed_query&f=live")  # Refresh the page after loading cookies
        sleep(3)
    else:
        username = input("Enter Username: ")
        password = input("Enter Password: ")
        login_to_twitter(browser, username, password)

    # To store the collected tweets
    all_tweets = []
    scroll_attempts = 0  # Track the number of scroll attempts

    while True:
        if scroll_attempts != 0:
            scroll_down(1000)
        sleep(3)  # Wait for tweets to load after scrolling

        # Grab all tweet articles
        tweets = find_all(S("//article[@role='article']"))

        # Extract text from each tweet and store it in the list
        if tweets:
            for tweet in tweets:
                tweet_text = tweet.web_element.text
                
                try:
                    time_element = tweet.web_element.find_element("tag name", "time")  # Get time in UTC of the tweet
                    tweet_time = time_element.get_attribute("datetime")

                    # Check if the tweet is within the user-specified timeframe
                    if not is_within_timeframe(tweet_time, cutoff_time):
                        print(f"Reached tweets older than {timeframe}, stopping...")
                        print(f"Total Collected Tweets: {len(all_tweets)}")
                        save_collected_tweets(all_tweets)
                        kill_browser()  # Close the browser
                        return malware, cutoff_time  # Stop scraping when reaching tweets older than the cutoff time

                    # If the tweet is within the timeframe, add it to the list
                    all_tweets.append(tweet_text)
                    print(f"Tweet Time: {tweet_time}")
                    print(f"Collected Tweet:\n{tweet_text}\n")

                except NoSuchElementException:
                    print("Skipped tweet due to missing time information")
                    continue

            scroll_attempts += 1  # Increase scroll attempts after processing tweets
        else:
            print("No more tweets found, stopping...")
            break

    print(f"Total Collected Tweets: {len(all_tweets)}")
    save_collected_tweets(all_tweets)
    kill_browser()  # Close the browser

    return malware, cutoff_time

# Function to save the collected tweets to a file
def save_collected_tweets(tweets):
    with open('collected_tweets.txt', 'w', encoding='utf-8') as collected_file:
        for tweet in tweets:
            collected_file.write(tweet + "\n")

# Main execution
if __name__ == "__main__":
    malware_name, cutoff_time = scrape_and_collect_tweets()
    main_extractor(malware_name, cutoff_time)
