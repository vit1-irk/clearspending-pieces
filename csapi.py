import json
import requests
import math
import pandas as pd
from dateutil import parser

def query_clearspending(base_url):
    print("Запрашиваем 1 страницу")
    results = []
    f = requests.get(base_url)
    try:
        contents = json.loads(f.text)
    except:
        return None

    results.extend(contents["contracts"]["data"])

    total = contents["contracts"]["total"]
    perpage = contents["contracts"]["perpage"]
    pages = math.ceil(total / perpage)
    
    print("Всего", total, "контрактов")
    if pages >= 2:
        for p in range(2, pages+1):
            print("Страница {0}/{1}".format(p, pages))
            f = requests.get(base_url + "&page=" + str(p))
            contents = json.loads(f.text)
            results.extend(contents["contracts"]["data"])
            
    return results

def pandas_ds(contracts):
    ds = []
    titles = ["Дата публикации", "ФЗ", "Цена, ₽", "Продукты", "Покупатель", "Подробнее"]

    for contract in contracts:
        if (contract.get("price") == None):
            continue
        ds.append((parser.parse(contract.get("publishDate")), contract.get("fz"), math.floor(contract.get("price")),\
                   ",".join((str(p.get("name")) for p in contract["products"])),\
                   contract["customer"]["fullName"], contract.get("printFormUrl")))

    ds.sort(key = lambda row: row[0].timestamp(), reverse=True)
    #print(titles, "\n")

    return pd.DataFrame(ds, columns=titles)

def escape_markup(txt):
    return str(txt).replace("<", "").replace(">", "")
    
def tg_formatting(pd_ds):
    txt = ""
    keys = pd_ds.keys()
    for row in pd_ds.values[0:3]:
        for key, i in zip(keys, range(len(keys))):
            txt += "<b>{0}:</b> {1}\n".format(key, escape_markup(row[i]))
        txt+="\n\n"

    return txt