# -*- coding: utf-8 -*-

import datetime
import logging as log

import secrets
from util import common
from webhook import BotUtils

bot = BotUtils.bot
messages = []


def process_day():
    """Questo comando verrà fatto partire alle 02:00 di ogni giorno.
    Questo comando scorre tutta la lista di utenti controllando i viaggi effettuati in giornata
    e addebitandogli il prezzo impostato in common.trip_price. Se il viaggio è temporaneo, vengono
    anche rimossi.
    """
    today = datetime.datetime.today()

    if 1 <= today.weekday() <= 5:
        for direction in "Salita", "Discesa":
            try:
                process_direction(direction)
            except Exception as ex:
                log.critical(ex)
                messages.append("Critical exception in {direction}")
                continue

    for item in messages:
        log.info(item)


def process_direction(direction):
    today = datetime.datetime.today()
    day = common.day_to_string(today.weekday() - 1)

    trip = secrets.groups[direction][day]
    for driver in trip:
        try:
            process_driver(direction, driver, trip)
        except Exception as ex:
            log.critical(ex)
            messages.append("Exception in: {direction}/{driver}")
            continue


def process_driver(direction, driver, trip):
    today = datetime.datetime.today()

    # Caso in cui il viaggio è sospeso
    if trip[driver]["Suspended"]:
        try:
            process_suspended_trip(direction, driver, trip)
        except Exception as ex:
            log.critical(ex)
            messages.append("Exception in suspension removal: {direction}/{driver}")

    # Caso normale, i passeggeri vanno addebitati
    elif (today - datetime.timedelta(days=1)).date() not in common.no_trip_days:
        try:
            process_money(direction, driver, trip)
        except Exception as ex:
            log.critical(ex)
            messages.append("Exception in debt processing: {direction}/{driver}")


def process_money(direction, driver, trip):
    today = datetime.datetime.today()
    day = common.day_to_string(today.weekday() - 1)

    # Prima addebito tutti gli utenti
    for mode in "Temporary", "Permanent":
        for user in trip[driver][mode]:
            try:
                secrets.users[user]["Debit"][driver] += common.trip_price
                if secrets.users[user]["Debit"][driver] == 0.0:
                    del secrets.users[user]["Debit"][driver]

                messages.append("Added trip cost: {common.dir_name(direction)} ")
            except KeyError:
                secrets.users[user]["Debit"][driver] = common.trip_price
            except Exception as ex:
                log.critical(ex)
                messages.append("Failed to update credit for user {user}")

            bot.send_message(chat_id=str(user),
                             text=f"Ti sono stati addebitati {str(common.trip_price)} EUR "
                                  f"da {str(secrets.users[driver]['Name'])}.")
            messages.append("Alerted driver for credit: u{user} d{driver} {common.dir_name(direction)}")
            bot.send_message(chat_id=str(driver),
                             text=f"Hai ora un credito di {str(common.trip_price)} EUR"
                                  f" da parte di {str(secrets.users[user]['Name'])}.")
            messages.append("Alerted user for debit: u{user} d{driver} {common.dir_name(direction)}")

    # Poi ripristino le persone sospese
    for user in trip[driver]["SuspendedUsers"]:
        occupied_slots = len(trip[driver]["Permanent"]) + len(trip[driver]["Temporary"])
        total_slots = secrets.drivers[driver]["Slots"]

        # Può capitare che altre persone occupino il posto alle persone sospese.
        # Bisogna gestire questo caso avvisando l'autista e il passeggero.
        if occupied_slots > total_slots:
            bot.send_message(chat_id=str(user),
                             text=f"ATTENZIONE: Non è stato possibile ripristinare"
                                  f" la tua prenotazione di {day.lower()} con "
                                  f"{secrets.users[driver]['Name']} "
                                  f"{common.dir_name(direction)}"
                                  f"; qualcun'altro ha occupato il tuo posto. "
                                  f"Contatta l'autista per risolvere il problema.")
            messages.append("Overbooking for: u{user} d{driver}  {common.dir_name(direction)}")
        # Caso normale, la persona è spostata su Permanent
        else:
            try:
                trip[driver]["Permanent"].append(user)
                trip[driver]["SuspendedUsers"].remove(user)
                messages.append("Book restored: {driver} {common.dir_name(direction)} {user}")
            except Exception as ex:
                log.critical(ex)
                messages.append("Error in restoring booking for: u{user} d{driver}  {common.dir_name(direction)}")

            bot.send_message(chat_id=str(user),
                             text=f"La prenotazione per {day.lower()} con "
                                  f"{secrets.users[driver]['Name']} "
                                  f"{common.dir_name(direction)} è di nuovo operativa.")
            messages.append("Alerted user for booking restored: u{user} d{driver} {common.dir_name(direction)}")
            bot.send_message(chat_id=str(driver),
                             text="La prenotazione di "
                                  f"{secrets.users[user]['Name']} per {day.lower()} "
                                  f"{common.dir_name(direction)} è stata ripristinata.")
            messages.append("Alerted driver for booking restored: u{user} d{driver}  {common.dir_name(direction)}")

    # Elimino eventuali persone temporanee
    try:
        trip[driver]["Temporary"] = []
        messages.append("Emptied temporary users: {driver} {common.dir_name(direction)}")
    except Exception as ex:
        log.critical(ex)
        messages.append("Failed to empty temporary users {driver} {common.dir_name(direction)}")

    # Cancello l'eventuale ritrovo del giorno
    try:
        del trip[driver]["Location"]
        messages.append("Removed location: {driver} {common.dir_name(direction)}")
    except KeyError:
        pass
    except Exception as ex:
        log.critical(ex)
        messages.append("Failed to remove location {driver} {common.dir_name(direction)}")


def process_suspended_trip(direction, driver, trip):
    today = datetime.datetime.today()
    day = common.day_to_string(today.weekday() - 1)

    trip[driver]["Suspended"] = False  # Rimuovo la sospensione del viaggio
    bot.send_message(chat_id=driver,
                     text=f"Il tuo viaggio di {day.lower()} "
                          f"{common.dir_name(direction)} è stato ripristinato.")
    messages.append("Restored: {common.dir_name(direction)} {driver}")

    for mode in "Temporary", "Permanent":
        for user in trip[driver][mode]:
            bot.send_message(chat_id=user,
                             text=f"Il viaggio di {secrets.users[driver]['Name']}"
                                  f" per {day.lower()} {common.dir_name(direction)}"
                                  f" è di nuovo operativo. La tua prenotazione "
                                  f"{common.mode_name(mode)} è di nuovo valida.")
            messages.append("Reminder sent:a {common.dir_name(direction)} {user}")


def weekly_report():
    """Questo comando viene fatto partire ogni sabato alle 12.00. Scorre tutta la lista di utenti e gli invia
    un messaggio con il riepilogo di soldi che devono dare. Se l'utente è anche un autista, riceverà anche
    un messaggio con i crediti.
    """
    from webhook import BotUtils
    bot = BotUtils.bot

    for user in secrets.users:
        # Invio dei debiti per tutti gli utenti
        try:
            debits = common.get_debits(user)
            if debits:
                message = ["Riepilogo settimanale dei debiti:\n"]
                for name, value in debits:
                    message.append(f"\n{secrets.users[name]['Name']} - {str(value)} EUR")
                bot.send_message(chat_id=user, text="".join(message))
        except Exception as ex:
            messages.append("Failed to alert user {user}")
            log.critical(ex)

        # Invio dei crediti per ogni singolo autista
        try:
            if user in secrets.drivers:
                credits = common.get_credits(user)
                if credits:
                    message = ["Riepilogo settimanale dei crediti:\n"]
                    for name, value in credits:
                        message.append(f"\n{secrets.users[name]['Name']} - {str(value)} EUR")
                    bot.send_message(chat_id=user, text="".join(message))
        except Exception as ex:
            messages.append("Failed to alert driver {user}")
            log.critical(ex)
