#!/usr/bin/env python3

import pandas as pd
import pdb
import sys
import csapi
import telebot
from telebot import util
from telebot.types import InlineKeyboardButton
from telegram_bot_pagination import InlineKeyboardPaginator
import traceback
import json

config = json.load(open("bot_config.json"))
bot = telebot.TeleBot(config["token"])
base_url = "http://openapi.clearspending.ru/restapi/v3/"

last_queries = {}
msgs_to_delete = {}

def set_last_query(message, value):
    if value == None:
        if str(message.chat.id) in last_queries.keys():
            del last_queries[str(message.chat.id)]
    else:
        last_queries[str(message.chat.id)] = value

def add_to_delete_buffer(message):
    if not str(message.chat.id) in msgs_to_delete.keys():
        msgs_to_delete[str(message.chat.id)] = []
    
    msgs_to_delete[str(message.chat.id)].append(message.id)

@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.send_message(message.chat.id, "Поиск по закупкам")

@bot.message_handler(commands=['products'])
def products_search(message):
    keys = [x.strip() for x in message.text.split(" ")[1:]]
    keys = [x for x in keys if x != ""]
    
    if len(keys) == 0:
        bot.send_message(message.chat.id, "Пустой запрос. Вводите ключевые слова в формате /команда слово слово")
        return
    
    kw_str = "+".join(keys)
    url = base_url + "contracts/search/?productsearch=" + kw_str
    set_last_query(message, url)
    send_character_page(message)

@bot.message_handler(commands=['customers'])
def customers_search(message):
    kw_str = "+".join(message.text.split(" ")[1:])
    url = base_url + "customers/search/?namesearch=" + kw_str
    
    bot.send_message(message.chat.id, url, parse_mode="HTML")

@bot.message_handler(commands=['suppliers'])
def suppliers_search(message):
    kw_str = "+".join(message.text.split(" ")[1:])
    url= base_url + "suppliers/search/?namesearch=" + kw_str
    
    bot.send_message(message.chat.id, url, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.split('#')[0]=='character')
def characters_page_callback(call):
    page = int(call.data.split('#')[1])
    
    add_to_delete_buffer(call.message)
    for mid in msgs_to_delete[str(call.message.chat.id)]:
        bot.delete_message(call.message.chat.id, mid)
    msgs_to_delete[str(call.message.chat.id)] = []
    
    send_character_page(call.message, page)

@bot.callback_query_handler(func=lambda call: call.data=='back')
def characters_go_back(call):
    set_last_query(call.message, None)
    msgs_to_delete[call.message.chat.id] = []
    
    bot.send_message(call.message.chat.id, "Введите новый запрос", parse_mode="HTML")

def send_character_page(message, page=1):
    url = last_queries[str(message.chat.id)]
    result, meta = csapi.query_clearspending_text(url, page)
    if meta == None or meta["pages"] == 1:
        set_last_query(message, None)
        bot.send_message(message.chat.id, result, parse_mode="HTML")
        return

    pieces = util.split_string(result, 3000)
    if len(pieces) > 1:
        for piece in pieces[:len(pieces)-2]:
            msg = bot.send_message(message.chat.id, piece, parse_mode="HTML")
            add_to_delete_buffer(msg)

    paginator = InlineKeyboardPaginator(
        meta["pages"],
        current_page=page,
        data_pattern='character#{page}')

    paginator.add_after(InlineKeyboardButton('Отмена', callback_data='back'))

    bot.send_message(
        message.chat.id,
        pieces[-1],
        reply_markup=paginator.markup,
        parse_mode='HTML')

def telegram_exception(e):
    print(str(e))

bot.polling()