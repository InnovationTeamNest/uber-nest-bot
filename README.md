# Uber NEST Bot

**Uber NEST Bot** is a Python-driven Telegram bot implementing the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) API, and run on a Google App Engine Standard environment.

This is the code powering [@ubernestbot](https://t.me/ubernestbot).

The Bot's purpose is to effortlessly mantain car sharing tasks within a small community (NEST, in this case).

Currently, documentation and localization is offered in Italian. Any effort to translate it in other languages is more than welcome.

## Sample secrets, dataset file

In order to make the bot work, a file named `dataset.py` must be placed inside the `data/` folder. It must contain:

```python
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

It is advisable to avoid using this file directly, and instead use the APIs found in the `data_api.py` file.

Another file, `secrets.py`, must be included in `data/` with the following data:

```python
# The Telegram token from BotFather:
bot_token = "..." 

# The owner chat id for debugging purposes:
owner_id = "..."

# The URL of the Google App Engine application, used for the Webhook:
url = "https://sample-name123456.appspot.com/"
 ```
 
## Contribute
Feel free to contribute by forking the project and issuing a pull request. Any contribution will be assessed by the NEST Innovation Team before merging the pull request.
