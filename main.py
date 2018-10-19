# -*- coding: utf-8 -*-
import logging as log
import sys

from flask import Flask, request

from secrets import bot_token

app = Flask(__name__)


@app.before_first_request
def init():
    # Inizializzo il logging
    log.basicConfig(level=log.DEBUG, format=' - %(levelname)s - %(name)s - %(message)s')


@app.route('/', methods=['GET'])
def index():
    return "UberNEST Bot is running!", 200


@app.route('/set_webhook', methods=['GET'])
def webhook():
    if 'X-Appengine-Cron' in request.headers:
        from webhook import dispatcher_setup, bot
        # Ogni volta che si carica una nuova versione, bisogna rifare il setup del bot!
        # Ciò viene automatizzato nelle richieste provenienti esclusivamente da Telegram.
        res = dispatcher_setup()
        if res:
            return "Success!", 200
        else:
            log.error("Errore nel reset del Webhook!")
            return "Webhook setup failed...", 500
    else:
        return "Access denied", 403


@app.route('/' + bot_token, methods=['POST'])
def update():
    import telegram
    from services.dumpable import dump_data
    from webhook import bot, process

    # De-Jsonizzo l'update
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    # Loggo il contenuto dell'update
    log.info(update)
    # Faccio processare al dispatcher l'update
    process(update)
    # Infine salvo eventuali dati modificati
    dump_data()

    return "See console for output", 200


@app.route('/data', methods=['GET'])
def data():
    from services.dumpable import get_data, print_data
    get_data()
    print_data()

    return "Data output in console.", 200


@app.route('/localscripts', methods=['GET'])
def script():
    # get_data()
    # print_data()
    # dump_data()

    return "", 403


@app.route('/night', methods=['GET'])
def night():
    if 'X-Appengine-Cron' in request.headers:
        from services.dumpable import get_data, dump_data
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
        from services.dumpable import get_data, dump_data
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
        from services.dumpable import get_data
        from services.reminders import remind

        get_data()
        remind()

        return "See console for output.", 200
    else:
        return "Access denied", 403
