# -*- coding: utf-8 -*-
from telegram import InlineQueryResultArticle, InputTextMessageContent

import secrets
from util import common

povo_url = "https://www.science.unitn.it/cisca/avvisi/titolo2.jpg"
nest_url = "http://giornaletrentino.it/image/policy:1.937279:1502009929/image/image.jpg"


def inline_handler(bot, update):
    query = update.inline_query.query
    chat_id = str(update.inline_query.from_user.id)
    if not query or chat_id not in secrets.users:
        return

    results = list()

    for day in common.work_days:
        for direction in "Salita", "Discesa":
            for driver in secrets.groups[direction][day]:
                driver_name = secrets.users[driver]['Name']
                if query.lower() in day.lower() or query.lower() in driver_name.lower():
                    # Bla Bla Bla Bla
                    trip = secrets.groups[direction][day][driver]
                    people = ', '.join([f"{secrets.users[user]['Name']}"
                                        for mode in trip
                                        if mode == "Temporary" or mode == "Permanent"
                                        for user in trip[mode]])
                    results.append(
                        InlineQueryResultArticle(
                            id=f"{direction}{day}{driver}",
                            title=f"{driver_name.split(' ')[-1]} {day} {common.dir_name(direction)}",
                            input_message_content=InputTextMessageContent(
                                f"\n\n🚗 {driver_name}"
                                f"{' - 🚫 Sospeso' if trip['Suspended'] else ''}"
                                f"\n🗓 {day}"
                                f"\n🕓 {trip['Time']}"
                                f"\n{common.dir_name(direction)}"
                                f"\n👥 {people}"),
                            hide_url=True,
                            thumb_url=povo_url if direction == "Salita" else nest_url,
                            thumb_height=40,
                            thumb_width=40
                        )
                    )

    bot.answer_inline_query(update.inline_query.id, results)
