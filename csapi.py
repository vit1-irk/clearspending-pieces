import json
import requests
import math
import pandas as pd
from dateutil import parser
import traceback

def query_clearspending_page(base_url, page=1, perpage=10):
    results = []
    f = requests.get(base_url + "&page={0}&perpage={1}&sort=signDate".format(page, perpage))
    try:
        contents = json.loads(f.text)
    except:
        return None

    results.extend(contents["contracts"]["data"])

    total = contents["contracts"]["total"]
    perpage = contents["contracts"]["perpage"]
    pages = math.ceil(total / perpage)
            
    return results, {"total": total, "perpage": perpage, "pages": pages}

def query_clearspending(base_url):
    results, meta = query_clearspending_page(base_url, perpage=50)
    if results == None:
        return None
    
    print("Всего", meta["total"], "контрактов")
    if meta["pages"] >= 2:
        for p in range(2, pages+1):
            print("Страница {0}/{1}".format(p, meta["pages"]))
            res2, meta2 = query_clearspending_page(base_url, p, meta["perpage"])
            if res2 == None:
                break
            
            results.extend(res2)
    return results


def pandas_ds(contracts):
    ds = []
    titles = ["Дата публикации", "ФЗ", "Цена, ₽", "Продукты", "Покупатель", "Подробнее"]

    for contract in contracts:
        if (contract.get("price") == None):
            continue
        customer = contract.get("customer")
        if customer != None:
            customer = customer.get("fullName")
            
        products_arr = contract.get("products")
        products = []
        for p in products_arr:
            if not "name" in p.keys():
                products.append(str(p.get("additionalInfo")))
            else:
                products.append(str(p.get("name")))
        
        ds.append((parser.parse(contract.get("publishDate")), contract.get("fz"), math.floor(contract.get("price")),\
                   ",".join(products),\
                   customer, contract.get("printFormUrl")))

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
            row_escaped = escape_markup(row[i])
            if len(row_escaped) > 250:
                row_escaped = row_escaped[0:250]
            txt += "<b>{0}:</b> {1}\n".format(key, row_escaped)
        txt+="\n\n"

    return txt

def query_clearspending_text(base_url, page=1, perpage=10):
    try:
        result, meta = query_clearspending_page(base_url, page, perpage)
        if result == None:
            return "clearspending api выдало пустой ответ", None
        
        pd_ds = pandas_ds(result)
        text_to_send = tg_formatting(pd_ds)
        return text_to_send, meta

    except Exception as e:
        traceback.print_exc()
        return str(e), None