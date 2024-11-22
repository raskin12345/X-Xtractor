import os
import pickle
from time import sleep
from datetime import datetime, timedelta
from dateutil import parser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to save cookies to a file
def save_cookies(driver):
    with open("cookies.pkl", "wb") as file:
        pickle.dump(driver.get_cookies(), file)

# Function to load cookies from a file
def load_cookies(driver):
    if os.path.exists("cookies.pkl"):
        with open("cookies.pkl", "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)

# Function to calculate the cutoff time based on the user-defined timeframe
def calculate_cutoff_time(timeframe):
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

# Function to check if a tweet is within the specified timeframe
def is_within_timeframe(tweet_time_str, cutoff_time):
    try:
        tweet_time = parser.isoparse(tweet_time_str).replace(tzinfo=None)
        return tweet_time >= cutoff_time
    except Exception as e:
        print(f"Error parsing tweet time: {e}")
        return False

# Function to scroll down the page
def scroll_down(driver):
    driver.execute_script("window.scrollBy(0, 1000);")

# Main function to scrape and collect tweets
def scrape_and_collect_tweets():
    malware = input("Enter the hashtag to search for: ")
    timeframe = input("Enter the timeframe (e.g., '7 days', '3 hours', '2 weeks'): ")

    cutoff_time = calculate_cutoff_time(timeframe)
    print(f"Scraping tweets from the last {timeframe}, cutoff time: {cutoff_time}")

    # Start the browser
    driver = webdriver.Firefox()  # Ensure geckodriver is installed
    driver.get(f"https://x.com/search?q=%23{malware}&src=typed_query&f=live")
    sleep(3)

    # Load cookies if they exist
    if os.path.exists("cookies.pkl"):
        load_cookies(driver)
        driver.refresh()
        sleep(3)
    else:
        username = input("Enter Username: ")
        password = input("Enter Password: ")

        # Log in to Twitter (X)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "session[username_or_email]"))
            ).send_keys(username)
            driver.find_element(By.NAME, "session[password]").send_keys(password)
            driver.find_element(By.XPATH, "//div[contains(text(),'Log in')]").click()
            sleep(5)
            save_cookies(driver)
        except TimeoutException:
            print("Login failed. Please check your credentials.")
            driver.quit()
            return

    all_tweets = []
    scroll_attempts = 0

    while True:
        if scroll_attempts > 0:
            scroll_down(driver)
        sleep(3)

        try:
            # Locate all tweet elements
            tweets = driver.find_elements(By.XPATH, "//article[@role='article']")

            if not tweets:
                print("No more tweets found, stopping...")
                break

            for tweet in tweets:
                tweet_text = tweet.text
                try:
                    time_element = tweet.find_element(By.TAG_NAME, "time")
                    tweet_time = time_element.get_attribute("datetime")
                except NoSuchElementException:
                    continue

                if not is_within_timeframe(tweet_time, cutoff_time):
                    print(f"Reached tweets older than {timeframe}, stopping...")
                    driver.quit()
                    with open('collected_tweets.txt', 'w', encoding='utf-8') as file:
                        file.writelines(f"{line}\n" for line in all_tweets)
                    return

                all_tweets.append(tweet_text)
                print(f"Collected Tweet:\n{tweet_text}\n")

            scroll_attempts += 1

        except Exception as e:
            print(f"Error during scraping: {e}")
            break

    print("Total Collected Tweets:", len(all_tweets))
    with open('collected_tweets.txt', 'w', encoding='utf-8') as file:
        file.writelines(f"{line}\n" for line in all_tweets)

    driver.quit()
    return

if __name__ == "__main__":
    scrape_and_collect_tweets()
