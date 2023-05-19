"""
references:
https://github.com/israel-dryer/Twitter-Scraper/blob/main/scrapper.py
https://medium.com/@amardeepchauhan/selenium-tweepy-to-scrap-tweets-from-tweeter-and-analysing-sentiments-1804db3478ac
"""

import csv
from getpass import getpass
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Edge, EdgeOptions
from selenium.webdriver.common.by import By
from textblob import TextBlob
import re
import numpy as np
import pandas as pd
import pdb


def login(driver):
    '''
    Selenium 4.3.0
    * Deprecated find_element_by_* and find_elements_by_* are now removed (#10712)
    https://stackoverflow.com/questions/72754651/attributeerror-webdriver-object-has-no-attribute-find-element-by-xpath
    '''
    driver.get('https://twitter.com/i/flow/login')
    sleep(2)

    username_part = driver.find_element("xpath", '//input[@name="text"]')
    username_part.click()
    sleep(2)
    username_part.send_keys('bite7gx@gmail.com')
    sleep(2)

    driver.find_element("xpath",
                        '//div[@class="css-18t94o4 css-1dbjc4n r-sdzlij r-1phboty r-rs99b7 r-ywje51 r-usiww2 r-2yi16 r-1qi8awa r-1ny4l3l r-ymttw5 r-o7ynqc r-6416eg r-lrvibr r-13qz1uu"]').click()

    # # If encounter unusual activity
    # username_verification = driver.find_element("xpath", '//input[@name="text"]')
    # username_verification.click()
    # sleep(1)
    # username_verification.send_keys("not_sober_today")
    # driver.find_element("xpath", '//div[@class="css-901oao r-1awozwy r-6koalj r-18u37iz r-16y2uox r-37j5jr r-a023e6 r-b88u0q r-1777fci r-rjixqe r-bcqeeo r-q4m81j r-qvutc0"]').click()

    my_password = getpass(prompt='Twitter pwd: ')
    password = driver.find_element("xpath", '//input[@name="password"]')
    sleep(2)
    password.send_keys(my_password)

    driver.find_element("xpath", '//span[@class="css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0"]').click()

    password.send_keys(Keys.RETURN)


def keyword_scrape(driver, keyword, advanced_option="all"):
    # https://stackoverflow.com/questions/46669850/using-aria-label-to-locate-and-click-an-element-with-python3-and-selenium
    # can't find element by xpath

    # url = 'https://twitter.com/search'
    url = 'https://twitter.com/search-advanced?'
    driver.get(url)
    driver.maximize_window()
    sleep(5)

    if advanced_option == "all":
        search_twitter = driver.find_element("xpath", '//input[@name="allOfTheseWords"]')
    elif advanced_option == "exact":
        search_twitter = driver.find_element("xpath", '//input[@name="thisExactPhrase"]')
    elif advanced_option == "any":
        search_twitter = driver.find_element("xpath", '//input[@name="anyOfTheseWords"]')
    elif advanced_option == "none":
        search_twitter = driver.find_element("xpath", '//input[@name="noneOfTheseWords"]')

    # search_twitter.click()
    search_twitter.send_keys(keyword)
    search_twitter.send_keys(Keys.RETURN)
    sleep(5)

    return True


def change_page_by_tab(driver, tab_name="Top"):
    # choose between "top"/"latest" tweets
    tab = driver.find_element(by=By.LINK_TEXT, value=tab_name)
    tab.click()
    xpath_tab_state = f'//a[contains(text(),\"{tab_name}\") and @aria-selected=\"true\"]'
    sleep(5)
    return xpath_tab_state


def sentiment_analysis(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0:
        return 'positive'
    elif analysis.sentiment.polarity < 0:
        return 'negative'
    else:
        return 'neutral'


def scroll_down_page(driver, last_position, num_seconds_for_loading=2, max_attempts=5):
    """
    This function will try to scroll down the page until it reaches the max_attempt, which means
    there is either a network problem or there is nothing more to show.
    :param driver:
    :param last_position:
    :param num_seconds_for_loading:
    :param max_attempts:
    :return:
    """
    scroll_attempt = 0
    driver.execute_script('window.alert = function() {};')
    # To stop "notification" DOM pop-up
    # https://stackoverflow.com/a/27270456
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    sleep(num_seconds_for_loading)
    while scroll_attempt <= max_attempts:
        curr_position = driver.execute_script("return window.pageYOffset;")
        if curr_position == last_position:
            break
        scroll_attempt += 1
        last_position = curr_position

    return last_position


def collect_tweets_from_current_page(driver, lookback_limit=10):
    df = pd.DataFrame(columns=["cleaned_tweet", "sentiment"])
    page_cards = driver.find_elements("xpath", '//article[@data-testid="tweet"]')
    print(page_cards)
    if len(page_cards) > lookback_limit:
        page_cards = page_cards[-lookback_limit:]
    for card in page_cards:
        tweet = clean_tweets(card.text)
        sentiment = sentiment_analysis(tweet)
        curr_dict = {"cleaned_tweet": tweet,
                     "sentiment": sentiment}
        curr_df = pd.DataFrame([curr_dict])
        df = df.append(curr_df, ignore_index=True)

    return df


def clean_tweets(tweet):
    '''
    This function is to remove user name and links from any tweet.
    https://www.datasnips.com/59/remove-usernames-http-links-from-tweet-data/
    :param tweet:
    :return: clean text
    '''
    tweet = re.sub('@[^\s]+', '', tweet)
    tweet = re.sub('http[^\s]+', '', tweet)
    return tweet


if __name__ == '__main__':
    options = EdgeOptions()
    options.use_chromium = True
    curr_driver = Edge(options=options)

    # login(curr_driver)
    # sleep(5)
    keyword_scrape(curr_driver, "bank SVB")
    change_page_by_tab(curr_driver, tab_name="Latest")

    tweet_df = pd.DataFrame(columns=["cleaned_tweet", "sentiment"])

    last_pos = None
    while True and tweet_df.shape[0] < 100:
        try:
            curr_driver.find_element("xpath", '//div[@data-testid="interstitialGraphic"]')
            close_notification_window = \
                curr_driver.find_element("xpath",
                                    '//*[name()="svg" and @class="r-18jsvk2 r-4qtqp9 r-yyyyoo r-z80fyv r-dnmrzs r-bnwqim r-1plcrui r-lrvibr r-19wmn03"]')
            close_notification_window.click()
        except NoSuchElementException:
            pass

        df = collect_tweets_from_current_page(curr_driver)
        tweet_df = tweet_df.append(df, ignore_index=True)
        curr_pos = scroll_down_page(curr_driver, last_pos)
        if curr_pos == last_pos:
            break
        else:
            last_pos = curr_pos

    try:
        # print("Percentage of positive tweets: ", (1 - tweet_df['sentiment'].value_counts()['negative'] / tweet_df.shape[0]))
        print("Percentage of positive tweets: ",
              (tweet_df['sentiment'].value_counts()['positive'] / tweet_df.shape[0]))
    except KeyError:
        print("Percentage of positive tweets: 0%")
    # pdb.set_trace()
