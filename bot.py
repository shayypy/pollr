# Loop
import datetime
import time

# Twitter
import json
import tweepy

secrets = json.load(open('secrets.json'))

client = tweepy.Client(
    consumer_key=secrets['api_key'],
    consumer_secret=secrets['api_key_secret'],
    access_token=secrets['access_token'],
    access_token_secret=secrets['access_token_secret'],
)

def tweet_loop():
    days = json.load(open('days.json'))
    if not days:
        latest = {
            'date': [1970, 1, 1],
            'tweet_id': '0',
            'number': 0,
            'poll': {},  # https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/poll
        }
    else:
        latest = days[-1]

    today = datetime.date.today()
    if datetime.date(*latest['date']) >= today:
        # We usually shouldn't be here

        # See if we can wait until exactly when the latest poll is over
        if latest['poll']:
            if latest['poll']['voting_status'] != 'closed':
                end_datetime = datetime.datetime.fromisoformat(latest['poll']['end_datetime'])
                now = datetime.datetime.utcnow()
                time_until_over = (end_datetime - now).seconds
                print(f'#{latest["number"]} is still active, sleeping until it is over ({time_until_over}s)')
                time.sleep(time_until_over)
            else:
                time.sleep(60 * 60)
                return
        else:
            time.sleep(60 * 60)
            return

    new_number = latest['number'] + 1

    if latest['tweet_id']:
        previous_tweet = client.get_tweet(
            latest['tweet_id'],
            expansions=['attachments.poll_ids'],
            poll_fields=['end_datetime', 'voting_status'],
            user_auth=True,
        )
        poll = previous_tweet.includes['polls'][0]
        poll_data = {
            'id': str(poll.id),
            'options': poll.options,
            'end_datetime': poll.end_datetime.isoformat(),
            'voting_status': poll.voting_status,
        }
        latest['poll'] = poll_data

    poll_duration = 1440  # 1 day, in minutes
    time_until_over = poll_duration * 60

    response = client.create_tweet(
        text=f'pollr {new_number:,}',
        poll_options=['1', '2', '3', '4'],
        poll_duration_minutes=poll_duration,
        user_auth=True,
    )
    print(f'Tweeted pollr #{new_number}')

    # Store our new tweet
    data = {
        'tweet_id': str(response.data['id']),
        'date': [today.year, today.month, today.day],
        'number': new_number,
        'poll': {
            'id': None,
            'options': [
                {'position': 1, 'label': '1', 'votes': 0},
                {'position': 2, 'label': '2', 'votes': 0},
                {'position': 3, 'label': '3', 'votes': 0},
                {'position': 4, 'label': '4', 'votes': 0},
            ],
            'end_datetime': (datetime.datetime.utcnow() + datetime.timedelta(seconds=time_until_over)).isoformat(),
            'voting_status': 'open',
        }
    }
    days.append(data)
    json.dump(days, open('days.json', 'w'))

    print(f'Sleeping until poll is over (in {time_until_over}s)')
    time.sleep(time_until_over)

while True:
    tweet_loop()
