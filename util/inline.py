# -*- coding: utf-8 -*-
from telegram import InlineQueryResultArticle, InputTextMessageContent

import secrets
from util import common


def inline_handler(bot, update):
    query = update.inline_query.query.lower()
    chat_id = str(update.inline_query.from_user.id)
    if not query or chat_id not in secrets.users:
        return

    results = []

    for day in common.work_days:
        for direction in "Salita", "Discesa":
            for driver in secrets.groups[direction][day]:
                driver_name = secrets.users[driver]['Name']
                if query in day.lower() or query in driver_name.lower():
                    # Visualizzo solo le query contenenti giorno o autista
                    trip = secrets.groups[direction][day][driver]
                    people = ', '.join([f"{secrets.users[user]['Name']}" for mode in trip
                                        if mode == "Temporary" or mode == "Permanent" for user in trip[mode]])
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
                                f"\n👥 {people}"
                            ),
                            hide_url=True,
                            thumb_url=common.povo_url if direction == "Salita" else common.nest_url,
                            thumb_height=40,
                            thumb_width=40
                        )
                    )

    bot.answer_inline_query(update.inline_query.id, results)
