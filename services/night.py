# -*- coding: utf-8 -*-

import datetime
import logging as log

from data.data_api import get_trip_group, get_name, is_driver, all_users, get_slots, set_single_debit, \
    get_single_debit, remove_single_debit, get_debit_tuple, get_credits
from routing.webhook import BotUtils
from util import common

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
                messages.append(f"⚠ Exception in {direction}")
                continue

    for item in messages:
        log.info(item)


def process_direction(direction):
    today = datetime.datetime.today()
    day = common.day_to_string(today.weekday() - 1)

    trip = get_trip_group(direction, day)
    for driver in trip:
        try:
            process_driver(direction, driver, trip)
        except Exception as ex:
            log.critical(ex)
            messages.append(f"⚠ Exception in: {direction}/{driver}")
            continue


def process_driver(direction, driver, trip):
    today = datetime.datetime.today()

    # Caso in cui il viaggio è sospeso
    if trip[driver]["Suspended"]:
        try:
            process_suspended_trip(direction, driver, trip)
        except Exception as ex:
            log.critical(ex)
            messages.append(f"⚠ Exception in suspension removal: {direction}/{driver}")

    # Caso normale, i passeggeri vanno addebitati
    elif (today - datetime.timedelta(days=1)).date() not in common.no_trip_days:
        try:
            process_money(direction, driver, trip)
        except Exception as ex:
            log.critical(ex)
            messages.append(f"⚠ Exception in debit processing: {direction}/{driver}")


def process_money(direction, driver, trip):
    today = datetime.datetime.today()
    day = common.day_to_string(today.weekday() - 1)

    # Prima addebito tutti gli utenti
    for mode in "Temporary", "Permanent":
        for user in trip[driver][mode]:
            try:
                set_single_debit(user, driver, get_single_debit(user, driver) + common.trip_price)
                if get_single_debit(user, driver) == 0.0:
                    remove_single_debit(user, driver)

                messages.append(f"Added debit to u{user} from d{driver} {direction} ")
            except KeyError:
                set_single_debit(user, driver, common.trip_price)
            except Exception as ex:
                log.critical(ex)
                messages.append(f"⚠ Failed to update debits for u{user} from d{driver} {direction}")

            bot.send_message(chat_id=str(user),
                             text=f"Ti sono stati addebitati {str(common.trip_price)} EUR "
                                  f"da {str(get_name(driver))}.")
            messages.append(f"Alerted driver for credit: u{user} d{driver} {direction}")
            bot.send_message(chat_id=str(driver),
                             text=f"Hai ora un credito di {str(common.trip_price)} EUR"
                                  f" da parte di {str(get_name(user))}.")
            messages.append(f"Alerted user for debit: u{user} d{driver} {direction}")

    # Poi ripristino le persone sospese
    for user in trip[driver]["SuspendedUsers"]:
        occupied_slots = len(trip[driver]["Permanent"]) + len(trip[driver]["Temporary"])
        total_slots = get_slots(driver)

        # Può capitare che altre persone occupino il posto alle persone sospese.
        # Bisogna gestire questo caso avvisando l'autista e il passeggero.
        if occupied_slots > total_slots:
            bot.send_message(chat_id=str(user),
                             text=f"ATTENZIONE: Non è stato possibile ripristinare"
                                  f" la tua prenotazione di {day.lower()} con "
                                  f"{get_name(driver)} "
                                  f"{common.dir_name(direction)}"
                                  f"; qualcun'altro ha occupato il tuo posto. "
                                  f"Contatta l'autista per risolvere il problema.")
            messages.append(f"Overbooking for: u{user} d{driver}  {direction}")
        # Caso normale, la persona è spostata su Permanent
        else:
            try:
                trip[driver]["Permanent"].append(user)
                trip[driver]["SuspendedUsers"].remove(user)
                messages.append(f"Booking restored: u{user} d{driver} {direction}")
            except Exception as ex:
                log.critical(ex)
                messages.append(f"⚠ Error in restoring booking for: u{user} d{driver} {direction}")

            bot.send_message(chat_id=str(user),
                             text=f"La prenotazione per {day.lower()} con "
                                  f"{get_name(driver)} "
                                  f"{common.dir_name(direction)} è di nuovo operativa.")
            messages.append(f"Alerted user for booking restored: u{user} d{driver} {direction}")
            bot.send_message(chat_id=str(driver),
                             text="La prenotazione di "
                                  f"{get_name(user)} per {day.lower()} "
                                  f"{common.dir_name(direction)} è stata ripristinata.")
            messages.append(f"Alerted driver for booking restored: u{user} d{driver} {direction}")

    # Elimino eventuali persone temporanee
    try:
        trip[driver]["Temporary"] = []
        messages.append(f"Emptied temporary users: {driver} {direction}")
    except Exception as ex:
        log.critical(ex)
        messages.append(f"⚠ Failed to empty temporary users {driver} {direction}")

    # Cancello l'eventuale ritrovo del giorno
    try:
        del trip[driver]["Location"]
        messages.append(f"Removed location: {driver} {direction}")
    except KeyError:
        pass
    except Exception as ex:
        log.critical(ex)
        messages.append(f"⚠ Failed to remove location {driver} {direction}")


def process_suspended_trip(direction, driver, trip):
    today = datetime.datetime.today()
    day = common.day_to_string(today.weekday() - 1)

    trip[driver]["Suspended"] = False  # Rimuovo la sospensione del viaggio
    bot.send_message(chat_id=driver,
                     text=f"Il tuo viaggio di {day.lower()} "
                          f"{common.dir_name(direction)} è stato ripristinato.")
    messages.append(f"Restored trip: {direction} {driver}")

    for mode in "Temporary", "Permanent":
        for user in trip[driver][mode]:
            bot.send_message(chat_id=user,
                             text=f"Il viaggio di {get_name(driver)}"
                                  f" per {day.lower()} {common.dir_name(direction)}"
                                  f" è di nuovo operativo. La tua prenotazione "
                                  f"{common.mode_name(mode)} è di nuovo valida.")
            messages.append(f"Reminder sent for restored trip: u{user} d{driver} {direction}")


def weekly_report():
    """Questo comando viene fatto partire ogni sabato alle 12.00. Scorre tutta la lista di utenti e gli invia
    un messaggio con il riepilogo di soldi che devono dare. Se l'utente è anche un autista, riceverà anche
    un messaggio con i crediti.
    """

    for user in all_users():
        # Invio dei debiti per tutti gli utenti
        try:
            debits = get_debit_tuple(user)
            if debits:
                message = ["Riepilogo settimanale dei debiti:\n"]
                for name, value in debits:
                    message.append(f"\n{get_name(name)} - {str(value)} EUR")
                bot.send_message(chat_id=user, text="".join(message))
        except Exception as ex:
            messages.append(f"Failed to alert user {user}")
            log.critical(ex)

        # Invio dei crediti per ogni singolo autista
        try:
            if is_driver(user):
                credits_ = get_credits(user)
                if credits_:
                    message = ["Riepilogo settimanale dei crediti:\n"]
                    for name, value in credits_:
                        message.append(f"\n{get_name(name)} - {str(value)} EUR")
                    bot.send_message(chat_id=user, text="".join(message))
        except Exception as ex:
            messages.append(f"Failed to alert driver {user}")
            log.critical(ex)
