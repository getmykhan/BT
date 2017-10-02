""" Importing all the useful Dependencies """
import facebook
import time
import random
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from nltk.corpus import stopwords
import csv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from wordcloud import WordCloud
import pygal



def main():

    """ Enter the website name. i.e boredpanda.com """
    site_name = input("Enter the site here: ")
    try:
        html = requests.get('http://'+ site_name +'/sitemap.xml')
        html = html.url

    except:
        browser = webdriver.Chrome()
        browser.get('http://www.google.com')
        search = browser.find_element_by_name('q')
        search.send_keys('filetype:xml' + ' ' + 'site:'+ site_name + ' ' + 'inurl:sitemap')
        search.send_keys(Keys.RETURN)
        search_result = browser.find_element_by_css_selector('#rso > div > div > div > div > h3')
        if search_result:
            print("True")
        search_result.click()
        html = browser.current_url
        print(html)

    page = requests.get(html)
    print('Loaded page with: {}'.format(page))

    links = BeautifulSoup(page.content, 'html.parser')


    """ All the urls are written into a file """

    urls = [element.text for element in links.findAll('loc')]
    print('Found {:,} URLs in the sitemap'.format(len(urls)))
    links = []
    with open('sitemap_urls.dat', 'w') as f:
        for url in urls:
            links.append(url)
            f.write(url + '\n')

    """ Access token from the graph api explorer """
    # Access token to be changed or an error will be thrown
    acess_token = 'EAACEdEose0cBACf0PR3SIQRKIB5HOYXR955B7grSqZCalaqEYdd5aZCJtvIfrrVVZCMwlDKr4T2bwmallfCXToZCx8VR8LkFM9eQiacVVcwTdm4DB5Im1ykatuuUxBZChc4WLAlXR1R0ZBCMKd488Yh1q8RZCo9PwEhvD2kl4WblZACudH0dxkPBwHS5FBFnS0f55oZAAEvZCeZCgZDZD'
    graph = facebook.GraphAPI(acess_token, version=2.10)


    """ Go gain an extension period, use the below  """
    # id_app = "" ## Enter App id here
    # secret = "" ## secrey key goes here
    #extended_token = graph.extend_access_token(app_id=id_app, app_secret=secret)
    #print(extended_token)

    count = len(links)
    data_dic = {}

    # Iterate through all the urls and extract engagement measures

    for link in links:
        try:
            print("There are {} links left".format(count))
            attributes = []
            #freq = {}
            stop_lex = set(stopwords.words('English'))
            post_link = ("https://graph.facebook.com/" + link + '?access_token=' + acess_token)

            req = requests.get(post_link)
            req = req.json()
            # print(req)
            post_id = req['og_object']['id']
            post_like = (
            'https://graph.facebook.com/' + post_id + '/likes?summary=true&limit=0' + '&access_token=' + acess_token)
            like_req = requests.get(post_like)
            like_req = like_req.json()
            post_comments = (
            'https://graph.facebook.com/' + post_id + '/comments?summary=true&limit=0' + '&access_token=' + acess_token)
            comm_req = requests.get(post_comments)
            comm_req = comm_req.json()

            attributes.extend((req['share']['share_count'], like_req['summary']['total_count'],
                               comm_req['summary']['total_count'], req['og_object']['description'],
                               req['og_object']['title'], req['og_object']['type'],
                               req['og_object']['updated_time']
                               ))

            data_dic[post_id] = attributes
            time.sleep(random.random())

        except (KeyError) as e:
            print('Key error',e)
            pass
        except Exception as ex:
            print(ex)

        count -= 1

    
    # Writing all the scrapped data to data.csv

    print("WRITING TO CSV")
    with open('data.csv', 'w', encoding = "ISO-8859-1") as csv_file:
        dfd = csv.writer(csv_file)
        dfd.writerow(["POST_ID", "SHARES", "LIKES", "COMMENTS", "DESCRIPTION", "TITLE", "TYPE", "UPDATED_TIME"])
        for id, attr in data_dic.items():
            try:
                dfd.writerow([id, attr[0], attr[1], attr[2], attr[3], attr[4], attr[5], attr[6]])
            except:
                continue

    df = pd.read_csv('data.csv', sep=',', header=0, usecols=[0, 1, 2, 3, 4, 5, 6, 7], encoding = "ISO-8859-1")
    titles = pd.read_csv('data.csv', sep=',', header=0, usecols=[5], encoding = "ISO-8859-1")


    
    # Removing all the stopwords and non alphabetical character and obtaining keywords in all the titles

    stop_lex = set(stopwords.words('English'))
    bag_of_words = {}
    for index, row in titles.iterrows():
        title = row['TITLE'].lower().strip()
        title = re.sub('[^a-z]', ' ', title)
        words = title.split(' ')
        for word in words:
            if word in stop_lex:
                continue
            else:
                bag_of_words[word] = bag_of_words.get(word, 0) + 1

    
    # Obtaining the most frequent keywords
    bag_of_words = sorted(bag_of_words, key=bag_of_words.__getitem__, reverse=True)
    #print(bag_of_words)

    
    # This snippet is to create a string which will be used to generate the word cloud
    sting_word = ""
    for WORD in bag_of_words:
        sting_word = sting_word + WORD + " "
    print(sting_word)

    
    # Obtaining top 50 keywords
    words = []
    for i in range(50):
        words.append(bag_of_words[i])

    # Obtaining engagement measures for all the stories the keyword is present in.
    stats = {}
    for word in words:
        likes = 0
        shares = 0
        comments = 0
        measure = []
        for index, row in df.iterrows():
            title = row['TITLE'].lower().strip()
            title = re.sub('[^a-z]', ' ', title)
            title = title.split(' ')
            if word in title:
                likes = likes + row['LIKES']
                shares = shares + row['SHARES']
                comments = comments + row['COMMENTS']
        measure.append(likes)
        measure.append(shares)
        measure.append(comments)
        stats[word] = measure


    # writing statistics to stats.csv
    with open('stats.csv', 'w') as stats_csv:
        writer = csv.writer(stats_csv)
        writer.writerow(["WORD", "LIKES", "SHARES", "COMMENTS"])
        for id, attr in stats.items():
            writer.writerow([id, attr[0], attr[1], attr[2]])




    """ Word Cloud Representation of Keyword Density """

    wordcloud = WordCloud().generate(text=sting_word)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")

    wordcloud = WordCloud(max_font_size=40).generate(text=sting_word)
    plt.figure()
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.show()

    time.sleep(5)

    
    """ Creating an Interactive Normalized graph  """

    df = pd.read_csv('stats.csv')
    if isinstance(df.iloc[0, 0], float):
        df.drop(df.index[0], inplace=True)

    Top_Words = df['WORD']
    df.drop('WORD', axis=1, inplace=True)
    print(df.head())
    normalized_df = (df - df.min()) / (df.max() - df.min())
    normalized_df = normalized_df.iloc[0:10, :]
    print(normalized_df)
    likes = normalized_df['LIKES'].tolist()
    comments = normalized_df['COMMENTS'].tolist()
    shares = normalized_df['SHARES'].tolist()

    line_chart = pygal.Bar(x_title='Top Keywords', y_title='Normalized Frequency')
    line_chart.title = 'Keyword density Normalized'
    line_chart.x_labels = Top_Words.tolist()[0:10]
    line_chart.add('LIKES', likes)
    line_chart.add('SHARES', shares)
    line_chart.add('COMMENTS', comments)
    line_chart.render()
    line_chart.render_to_file('popularity.svg')

    

main()
