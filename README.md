# Uber NEST Bot

**Uber NEST Bot** is a Python-driven Telegram bot implementing the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) API, and run on a Google App Engine Standard environment.

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
groups = {}
users = {}
drivers = {}
```
## Contribute
Feel free to contribute by forking the project and issuing a pull request. Any contribution will be assessed by the NEST Innovation Team before merging the pull request.

## To-Do

* Insert information about implemented functionality
* Port the whole project to Python 3 (Standard GAE Environment)