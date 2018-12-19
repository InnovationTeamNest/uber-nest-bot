# -*- coding: utf-8 -*-
import logging as log

from flask import Flask, request

from data.secrets import bot_token

app = Flask(__name__)


@app.before_first_request
def first_request():
    from routing import webhook
    log.basicConfig(level=log.DEBUG, format=' - %(levelname)s - %(name)s - %(message)s')
    webhook.BotUtils()
    # Rinnovo la posizione del webhook
    webhook.BotUtils.set_webhook()
    # Infine faccio il setup del Dispatcher
    webhook.dispatcher_setup()


@app.route('/', methods=['GET'])
def index():
    return "UberNEST Bot is running!", 200


# @app.route('/set_webhook', methods=['GET'])
# def webhook():
#     if 'X-Appengine-Cron' in request.headers:
#         import webhook
#         # Rinnovo la posizione del webhook
#         webhook.BotUtils.set_webhook()
#         # Infine faccio il setup del Dispatcher
#         webhook.dispatcher_setup()
#         return "Success!", 200
#     else:
#         return "Access denied", 403


@app.route('/' + bot_token, methods=['POST'])
def update():
    import telegram
    from data.dumpable import dump_data, empty_dataset, get_data
    from routing.webhook import process, BotUtils

    if empty_dataset():
        log.critical("Operating with an empty dataset! Restoring...")
        get_data()

    # Evoco il bot
    # De-Jsonizzo l'update
    t_update = telegram.Update.de_json(request.get_json(force=True), BotUtils.bot)
    # log.info(t_update)
    # Faccio processare al dispatcher l'update
    process(t_update)
    # Infine salvo eventuali dati modificati; ci provo finché non vengono
    # lanciate eccezioni
    # while True:
    try:
        dump_data()
        log.info("Dumping data to database")
    except Exception as ex:
        log.critical("Failed to save data!")

    return "See console for output", 200


@app.route('/data', methods=['GET'])
def data():
    from data.dumpable import get_data, print_data
    get_data()
    print_data()

    return "Data output in console.", 200


@app.route('/localscripts', methods=['GET'])
def script():
    from data.dumpable import get_data, dump_data
    from data import dataset

    get_data()

    for direction in dataset.groups:
        trip = dataset.groups[direction]["Martedì"]

        for item in list(trip):
            print(trip[item])
            del trip[item]

    dump_data()

    return "", 403


@app.route('/night', methods=['GET'])
def night():
    if 'X-Appengine-Cron' in request.headers:
        from data.dumpable import get_data, dump_data
        from services.night import process_day

        get_data()
        process_day()
        dump_data()

        return "See console for output.", 200
    else:
        return "Access denied", 403


@app.route('/weekly_report', methods=['GET'])
def weekly():
    if 'X-Appengine-Cron' in request.headers:
        from data.dumpable import get_data, dump_data
        from services.night import weekly_report

        get_data()
        weekly_report()
        dump_data()

        return "See console for output.", 200
    else:
        return "Access denied", 403


@app.route('/reminders', methods=['GET'])
def reminders():
    if 'X-Appengine-Cron' in request.headers:
        from data.dumpable import get_data
        from services.reminders import remind

        get_data()
        remind()

        return "See console for output.", 200
    else:
        return "Access denied", 403
