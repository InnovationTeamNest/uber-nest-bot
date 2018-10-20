**WARNING** This is an archived version from 19/10/2018, the last version to be written in Python 2.7. You should check the `master` branch for the latest non-deprecated version.

# Uber NEST Bot

**Uber NEST Bot** is a Python-driven Telegram bot implementing the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) API, and run on a Google App Engine Standard environment.

This is the code powering [@ubernestbot](https://t.me/ubernestbot).

The Bot's purpose is to effortlessly mantain car sharing tasks within a small community (NEST, in this case).

## Sample secret_data.py file

In order to make the bot work, a file named secret_data.py must be placed inside the root folder. It must contain:

```python
# The Telegram token from BotFather:
bot_token = "..." 

# The owner chat id for debugging purposes:
owner_id = "..."

# The URL of the Google App Engine application, used for the Webhook:
url = "https://sample-name123456.appspot.com/"

# Three objects, containing user data. They can be left blank and will be filled in by the bot as people register and add their trip times.
groups = {
    "Salita": {
        "Lunedì": {
        
        }, "Martedì": {
            # same as above
        } # ...
    },
    "Discesa": {
        # same as above
    }
}
users = {}
drivers = {}
```
## Contribute
Feel free to contribute by forking the project and issuing a pull request. Any contribution will be assessed by the NEST Innovation Team before merging the pull request.
