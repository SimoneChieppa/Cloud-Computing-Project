import os
import argparse
import re
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
#from googletrans import Translator
from textblob import TextBlob
import snscrape.modules.twitter as sntwitter
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import seaborn as sns
from deep_translator import GoogleTranslator

def city(country):
    df = pd.read_csv('country_list.csv')
    capital = df[df['country'] == country]['capital'].item()
    return capital


def clean_tweet(tweet):
    '''
    Utility function to clean tweet text by removing links, special characters
    using simple regex statements.
    '''
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())


def get_tweet_sentiment(tweet):
    '''
    Utility function to classify sentiment of passed tweet
    using textblob's sentiment method
    '''
    # create TextBlob object of passed tweet text
    analysis = TextBlob(clean_tweet(tweet))
    # set sentiment
    if analysis.sentiment.polarity > 0:
        return 'positive'
    elif analysis.sentiment.polarity == 0:
        return 'neutral'
    else:
        return 'negative'


def percentage(part, whole):
    return 100 * float(part)/float(whole)


# Using TwitterSearchScraper to scrape data and append tweets to list
def searcher(word, nation):
    tweets_list1 = []
    ricerca = word+' near:'+nation
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(ricerca).get_items()):
        if i > 100:  # number of tweets you want to scrape
            break
        tweets_list1.append([tweet.date, tweet.id, tweet.content, tweet.user.username, tweet.replyCount,
                             tweet.likeCount, tweet.retweetCount, tweet.lang])  # declare the attributes to be returned
    # Creating a dataframe from the tweets list above
    tweets_df1 = pd.DataFrame(tweets_list1, columns=[
                              'Datetime', 'Tweet Id', 'Text', 'Username', 'Replies', 'Likes', 'Retweets', 'language'])

    return(tweets_df1)


def sentiment_analysis(word, nation, receiver_email):
    df = searcher(word, nation)
    # Translation to English
    translator = Translator()
    for i in range(len(df)):
        if isinstance(df['Text'][i], str) == True:
            #df.loc[i, 'Text'] = df.loc[i, 'Text'].replace('.', '. ')
            df.loc[i, 'Text'] = translator.translate(
                df['Text'][i], dest='en').text

    # Sentiment
    tweets = df['Text']
    positive = 0
    negative = 0
    neutral = 0
    tweet_list = []
    neutral_list = []
    negative_list = []
    positive_list = []
    noOfTweet = len(tweets)
    for tweet in tweets:
        text = clean_tweet(tweet)
        tweet_list.append(text)
        score = get_tweet_sentiment(tweet)
        if score == 'negative':
            negative_list.append(text)
            negative += 1
        elif score == 'positive':
            positive_list.append(text)
            positive += 1
        else:
            neutral_list.append(text)
            neutral += 1
    positive = percentage(positive, noOfTweet)
    negative = percentage(negative, noOfTweet)
    neutral = percentage(neutral, noOfTweet)
    positive = format(positive, '.1f')
    negative = format(negative, '.1f')
    neutral = format(neutral, '.1f')

    # Creating PieCart sentiment
    labels = ['Positive', 'Neutral', 'Negative']
    sizes = [positive, neutral, negative]
    colors = sns.color_palette('deep')
    plt.pie(sizes, labels=labels, colors=colors,
            autopct='%.0f%%', pctdistance=0.5, explode=[0.05]*3)
    plt.title('Sentiment Analysis Result')
    plt.axis('equal')
    plt.savefig(word+ '_'+ nation +"_sent.png")
    plt.clf()

    # Plot languages
    labels_lang = df['language'].unique().tolist()
    data_lang = []
    for el in labels_lang:
        a = df.loc[df['language'] == str(el), 'language'].count()
        data_lang.append(a)
        colors = sns.color_palette("Paired")
    plt.pie(data_lang, colors=colors, autopct='%.0f%%')
    plt.style.use('default')
    plt.legend(labels_lang)
    plt.title('tweet languages')
    plt.axis('equal')
    plt.savefig(word+ '_'+ nation+"_lang.png")

    # Tweet con più scalpore
    for i in range(len(df)):
        df.loc[i, 'score'] = df.loc[i, 'Replies'] + \
            df.loc[i, 'Likes'] + df.loc[i, 'Retweets']
    tweet_scalp = df.loc[df['score'].idxmax(), 'Text']
    max_score = df['score'].idxmax()

    # Temporal interval
    for i in range(len(df)):
        df.loc[i, 'time'] = df.loc[i, 'Datetime']#datetime.strptime(df.loc[i, 'Datetime'], "%H:%M:%S")
    time_1 = df['time'].min()
    time_2 = df['time'].max()
    time_interval = time_2 - time_1
    with open(word + '_' + nation + '.txt', 'w') as f:
        f.write(tweet_scalp)
        f.write(str(max_score))
        f.write(time_interval)
    sendEmail(word,country, receiver_email)


def sendEmail(word,nation, receiver_email):
    with open(word + '_' + nation + '.txt', 'r') as f:
        lines = [line.rstrip() for line in f]
    sender_email = "twitter_analyzer@hotmail.com"
    password = "Tw1tter@n@lyzer1"
    # receiver_email = "conti.1849300@studenti.uniroma1.it"
    message = MIMEMultipart("related")
    message["Subject"] = "Twitter Analysis Results"
    message["From"] = sender_email
    message["To"] = receiver_email
    html = """
    <html>
    <head></head>
        <body>
        <p>Hello, below you can find the results of the analysis on {word} you requested to the TTA, enjoy the reading!</p>
        <p>First of all the Tweets analyzed by the system belong in an interval of {time_interval} hours.</p>
        <p>But now let's go on with some chart!</p>
        <h3>Sentiment about {word}</h3>
        <p>The pie chart below shows the proportions of general sentiment about the {word} from more than 2000 tweets.</p>
        <img src="cid:image1" alt="Sentiment" style="width:640px;height:480px;"><br>
        <h3>Language of Tweets</h3>
        <p>The next chart is instead to see the language distribution among tweets.</p>
        <img src="cid:image2" alt="Language" style="width:640px;height:480px;"><br>   
        <h3>Most stir Tweet</h3>
        <p>Finally let's see the tweet that caused the most interactions! The following tweet obtained {max_score} interactions (retweets, likes and replies):</p>{tweet_scalp}
        </body>
    </html>
    """.format(word=word, time_interval=lines[2], tweet_scalp=lines[0], max_score = lines[1])
    # Record the MIME types of text/html.
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    message.attach(part2)

    # This example assumes the image is in the current directory
    fp = open(word +'_'+ nation+ '_sent.png', 'rb')
    msgImage1 = MIMEImage(fp.read())
    fp.close()

    fp = open(word +'_'+ nation+ '_lang.png', 'rb')
    msgImage2 = MIMEImage(fp.read())
    fp.close()

    # Define the image's ID as referenced above
    msgImage1.add_header('Content-ID', '<image1>')
    msgImage2.add_header('Content-ID', '<image2>')
    message.attach(msgImage1)
    message.attach(msgImage2)
    with smtplib.SMTP("smtp.office365.com", 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )


def main():
    # Parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', type=str, required=True)
    parser.add_argument('-e', type=str, required=True)
    parser.add_argument('-c', type=str, required=False,
                        default="United Kingdom")  # Global
    args = parser.parse_args()
    topic_val = args.t
    email_val = args.e
    country_val = args.c

    # Opens csv with city <-> country correspondence
    df = pd.read_csv('country_list.csv')
    df.rename(columns={"name": "city"}, inplace=True)
    country = city(country_val)

    # Start analysis
    if os.path.exists(topic_val + '_' + country +".txt"):
        sendEmail(topic_val, country, email_val)
    else:
        sentiment_analysis(topic_val, country, email_val)



    return


if __name__ == '__main__':
    main()
