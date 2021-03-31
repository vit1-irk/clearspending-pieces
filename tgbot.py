#!/usr/bin/env python3

import pandas as pd
import pdb
import sys
import csapi
import telebot
from telebot import util
import traceback
import json

config = json.load(open("bot_config.json"))
bot = telebot.TeleBot(config["token"])
base_url = "http://openapi.clearspending.ru/restapi/v3/"

@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.send_message(message.chat.id, "Поиск по закупкам")

@bot.message_handler(commands=['products'])
def products_search(message):
    kw_str = "+".join(message.text.split(" ")[1:])
    url = base_url + "contracts/search/?productsearch=" + kw_str
    
    try:
        result = csapi.query_clearspending(url)
        if result == None:
            bot.send_message(message.chat.id, "clearspending api выдало пустой ответ")
            
        pd_ds = csapi.pandas_ds(result)
        text_to_send = csapi.tg_formatting(pd_ds)
        pieces = util.split_string(text_to_send, 3000)
        for piece in pieces:
            bot.send_message(message.chat.id, piece, parse_mode="HTML")
    except Exception as e:
        traceback.print_exc()
        bot.send_message(message.chat.id, str(e))

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

def telegram_exception(e):
    print(str(e))

bot.polling()