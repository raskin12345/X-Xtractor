import re
from datetime import datetime, timedelta
import pickle
import os
from time import sleep
from dateutil import parser
from selenium.common.exceptions import NoSuchElementException
from helium import start_firefox, write, click, sleep, find_all, go_to, kill_browser

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
    if unit == 'days' or unit == 'day' or unit == 'd':
        return datetime.utcnow() - timedelta(days=number)
    elif unit == 'hours' or unit == 'hour' or unit == 'h':
        return datetime.utcnow() - timedelta(hours=number)
    elif unit == 'weeks' or unit == 'week' or unit == 'w':
        return datetime.utcnow() - timedelta(weeks=number)
    elif unit == 'months' or unit == 'month' or unit == 'm':  # Approximate to 30 days per month
        return datetime.utcnow() - timedelta(days=30 * number)
    elif unit == 'years' or unit == 'year' or unit == 'y': # 365 days per year
        return datetime.utcnow() - timedelta(days=365 * number)
    else:
        raise ValueError("Unsupported time unit")

# Function to check if a tweet is within the specified timeframe
def is_within_timeframe(tweet_time_str, cutoff_time):
    tweet_time = parser.isoparse(tweet_time_str).replace(tzinfo=None)  # Convert to offset-naive datetime object
    return tweet_time >= cutoff_time

# Function to scrape and collect tweets
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
        # Log in to Twitter (X)
        write(username, into="Phone, email, or username")
        click('Next')
        sleep(1)
        write(password, into='Password')
        click('Log in')
        sleep(5)  # Wait for login to complete

        # Save cookies after logging in for future use
        save_cookies(browser)

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
                except NoSuchElementException:
                    continue  # Skip the tweet if the time element is not found

                tweet_time = time_element.get_attribute("datetime")

                # Check if the tweet is within the user-specified timeframe
                if not is_within_timeframe(tweet_time, cutoff_time):
                    print(f"Reached tweets older than {timeframe}, stopping...")
                    print(f"Total Collected Tweets: {len(all_tweets)}")
                    kill_browser()  # Close the browser
                    # Save the tweets to a file
                    with open('collected_tweets.txt', 'w', encoding='utf-8') as collected_file:
                        for line in all_tweets:
                            collected_file.write(line + "\n")
                    return malware, cutoff_time  # Stop scraping when reaching tweets older than the cutoff time

                # If the tweet is within the timeframe, add it to the list
                all_tweets.append(tweet_text)
                print(f"Tweet Time: {tweet_time}")
                print(f"Collected Tweet:\n{tweet_text}\n")

            scroll_attempts += 1  # Increase scroll attempts after processing tweets
        else:
            print("No more tweets found, stopping...")
            break

    # After collecting tweets, print or save the results
    print("Total Collected Tweets:", len(all_tweets))

    # Save the tweets to a file
    with open('collected_tweets.txt', 'w', encoding='utf-8') as collected_file:
        for line in all_tweets:
            collected_file.write(line + "\n")
    
    return malware, cutoff_time
