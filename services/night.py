# -*- coding: utf-8 -*-

import datetime
import logging as log

import secrets
from util import common


def process_day():
    """Questo comando verrà fatto partire alle 02:00 di ogni giorno.
    Questo comando scorre tutta la lista di utenti controllando i viaggi effettuati in giornata
    e addebitandogli il prezzo impostato in common.trip_price. Se il viaggio è temporaneo, vengono
    anche rimossi.
    """
    from webhook import BotUtils
    bot = BotUtils.bot

    today = datetime.datetime.today()
    day = common.day_to_string(today.weekday() - 1)

    if 1 <= today.weekday() <= 5 and (today - datetime.timedelta(days=1)).date() not in common.no_trip_days:
        for direction in "Salita", "Discesa":
            trips = secrets.groups[direction][day]
            for driver in trips:
                # Caso in cui il viaggio è sospeso
                if trips[driver]["Suspended"]:
                    trips[driver]["Suspended"] = False  # Rimuovo la sospensione del viaggio
                    bot.send_message(chat_id=driver,
                                     text=f"Il tuo viaggio di {day.lower()} "
                                          f"{common.dir_name(direction)} è stato ripristinato.")

                    for mode in "Temporary", "Permanent":
                        for user in trips[driver][mode]:
                            bot.send_message(chat_id=user,
                                             text=f"Il viaggio di {secrets.users[driver]['Name']}"
                                                  f" per {day.lower()} {common.dir_name(direction)}"
                                                  f" è di nuovo operativo. La tua prenotazione "
                                                  f"{common.mode_name(mode)} è di nuovo valida.")

                # Caso normale, i passeggeri vanno addebitati
                else:
                    # Prima addebito tutti gli utenti
                    for mode in "Temporary", "Permanent":
                        for user in trips[driver][mode]:
                            try:
                                secrets.users[user]["Debit"][driver] += common.trip_price
                            except KeyError:
                                secrets.users[user]["Debit"][driver] = common.trip_price

                            bot.send_message(chat_id=str(user),
                                             text=f"Ti sono stati addebitati {str(common.trip_price)} EUR "
                                                  f"da {str(secrets.users[driver]['Name'])}.")
                            bot.send_message(chat_id=str(driver),
                                             text=f"Hai ora un credito di {str(common.trip_price)} EUR"
                                                  f" da parte di {str(secrets.users[user]['Name'])}.")

                    # Poi ripristino le persone sospese
                    for user in trips[driver]["SuspendedUsers"]:
                        occupied_slots = len(trips[driver]["Permanent"]) + len(trips[driver]["Temporary"])
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
                        # Caso normale, la persona è spostata su Permanent
                        else:
                            trips[driver]["Permanent"].append(user)
                            trips[driver]["SuspendedUsers"].remove(user)

                            bot.send_message(chat_id=str(user),
                                             text=f"La prenotazione per {day.lower()} con "
                                                  f"{secrets.users[driver]['Name']} "
                                                  f"{common.dir_name(direction)} è di nuovo operativa.")
                            bot.send_message(chat_id=str(driver),
                                             text="La prenotazione di "
                                                  f"{secrets.users[user]['Name']} per {day.lower()} "
                                                  f"{common.dir_name(direction)} è stata ripristinata.")

                    # Elimino eventuali persone temporanee
                    trips[driver]["Temporary"] = []

                    # Cancello l'eventuale ritrovo del giorno
                    try:
                        del trips[driver]["Location"]
                    except KeyError:
                        continue


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
            log.critical(f"Failed to alert user {user}")
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
            log.critical(f"Failed to alert driver {user}")
            log.critical(ex)
