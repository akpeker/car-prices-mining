#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 17 17:30:55 2020

@author: kadir
"""
import time
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

URLBASE = r"https://www.sahibinden.com"
URLRELS = {
    "corolla-all": r"/toyota-corolla?pagingSize=50",
    "civic-all": r"/honda-civic?pagingSize=50",
    "egea-all": r"/fiat-egea?pagingSize=50",
    "focus-all": r"/ford-focus?pagingSize=50",
    "megane-all": r"/renault-megane?pagingSize=50",
    "octavia-all": r"/skoda-octavia?pagingSize=50",
    "passat-all": r"/volkswagen-passat?pagingSize=50",
    "corolla-auto": r"/toyota-corolla/yari-otomatik,otomatik?pagingSize=50",
    "civic-auto": r"/honda-civic/yari-otomatik,otomatik?pagingSize=50",
    "egea-auto": r"/fiat-egea/yari-otomatik,otomatik?pagingSize=50",
    "focus-auto": r"/ford-focus/yari-otomatik,otomatik?pagingSize=50",
    "megane-auto": r"/renault-megane/yari-otomatik,otomatik?pagingSize=50",
    "octavia-auto": r"/skoda-octavia/yari-otomatik,otomatik?pagingSize=50",
    "passat-auto": r"/volkswagen-passat/yari-otomatik,otomatik?pagingSize=50",
}
url = URLBASE + URLRELS["corolla-all"]

localpage = (
    r"./pages-downloaded/Toyota Corolla Fiyatları & Modelleri sahibinden.com'da.html"
)
localpage = r"./pages-downloaded/Toyota Corolla Fiyatları & Modelleri sahibinden.com'da - 20.html"


def process_listings(urlrels=URLRELS):
    for model in URLRELS:
        print("=" * 80, "\n", model, "\n", "-" * 80)
        df = listings_all_pages(URLRELS[model])
        filename = "{}_{}.xlsx".format(model, datetime.today().strftime("%Y-%m-%d"))
        df.to_excel(filename)


def listings_all_pages(urlrel=URLRELS["corolla-all"]):
    """Extract all listings pages, given the first page's URL, into a DataFrame"""
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "st=a267610bc71b147b787ef2b66276c71ff8cf4c89ec0985aa38a49c2d8fd10e68e8b41bd410e286458d94e00f18ca492510f5c612a38a1c56e; vid=623; cdid=QFx6W15Wcyfb5n0y5ec14ab9; segIds=; __gfp_64b=ExVldgP6W8jNGwyydK2uqiOYlzXA_6M3GlfHpkvXEh7.47; __gads=ID=5f0047c3884e13ed:T=1589725882:S=ALNI_Mb_FONeOpTtR8EZleu0ovv_JuckXw; _fbp=fb.1.1589725884070.526222377; _ga=GA1.2.1611957702.1589725883; _gid=GA1.2.1518436171.1589725885; nwsh=std; showPremiumBanner=false; MS1=https://www.sahibinden.com/kategori/otomobil; s4IssGuY1=A6Z_ICNyAQAA_Y7mbkf8fz5wRUCloFTU_CA9sbsSOwIWcCqe5dcNLjCJaaOoAcOOE7euclwgwH8AADQwAAAAAA==; _gali=searchResultsSearchForm",
        "Host": "www.sahibinden.com",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
    }

    infolist = []
    urlrel_next = urlrel
    while urlrel_next != "":
        url = URLBASE + urlrel_next
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print(f"WARNING: STATUS CODE = {r.status_code} at URL={urlrel_next}")
        data = r.text.replace("\n", "")
        soup = BeautifulSoup(data)
        infolist.extend(extract_list(soup))

        pg = soup.find(id="currentPageValue")["value"]
        nxt = soup.find(title="Sonraki")
        if nxt:
            urlrel_next = nxt["href"]
        else:
            urlrel_next = ""
        print(
            "page: {} [{}]".format(
                pg, "NEXT:" + urlrel_next if urlrel_next else "--LAST--"
            )
        )
        time.sleep(2)

    df = pd.DataFrame(infolist)
    return df


def extract_list(soup, verbose=0):
    """Extract listing items from given soup page, and return an infolist
    (a list of dictionaries containing info for each listing) which can then
    easily be converted to a DataFrame.
    """
    infolist = []
    for i, resitem in enumerate(soup.select("tr[class*='searchResultsItem']")):
        cells = resitem.find_all("td")
        if len(cells) < 10:
            if verbose:
                print(f"WARNING: Skipping tr:{i}")
                print(resitem)
            continue
        info = {}
        info["ID"] = resitem["data-id"]
        info["model"] = cells[1].get_text().strip()
        info["title"] = cells[2].get_text().strip()
        info["year"] = try_int(cells[3].get_text().strip())
        info["KM"] = try_int(cells[4].get_text().strip().replace(".", ""))
        info["color"] = cells[5].get_text().strip()
        price_cur = cells[6].get_text().strip().replace(".", "")
        info["price"] = try_int(price_cur.split()[0])
        info["currency"] = price_cur.split()[1]
        cnt = 1
        for x in cells[8].children:
            if isinstance(x, str):  # ['Kırşehir', <br/>, 'Merkez'] 1st and 3rd elems
                info[f"city{cnt}"] = x.strip()
                cnt += 1
            elif (
                x.get_text() != ""
            ):  # ['İzmir', <br>Aliağa</br>] 2nd elem is Tag with text
                info[f"city{cnt}"] = x.get_text().strip()
                cnt += 1
        info["detay-url"] = cells[0].find("a").get("href")
        infolist.append(info)

    return infolist


def try_int(x):
    """Safely convert anything that can be converted to int"""
    try:
        return int(x)
    except ValueError:
        return x


def dene2():
    """Extract 1 listings page, given as a URL, into a DataFrame"""
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "st=a267610bc71b147b787ef2b66276c71ff8cf4c89ec0985aa38a49c2d8fd10e68e8b41bd410e286458d94e00f18ca492510f5c612a38a1c56e; vid=623; cdid=QFx6W15Wcyfb5n0y5ec14ab9; segIds=; __gfp_64b=ExVldgP6W8jNGwyydK2uqiOYlzXA_6M3GlfHpkvXEh7.47; __gads=ID=5f0047c3884e13ed:T=1589725882:S=ALNI_Mb_FONeOpTtR8EZleu0ovv_JuckXw; _fbp=fb.1.1589725884070.526222377; _ga=GA1.2.1611957702.1589725883; _gid=GA1.2.1518436171.1589725885; nwsh=std; showPremiumBanner=false; MS1=https://www.sahibinden.com/kategori/otomobil; s4IssGuY1=A6Z_ICNyAQAA_Y7mbkf8fz5wRUCloFTU_CA9sbsSOwIWcCqe5dcNLjCJaaOoAcOOE7euclwgwH8AADQwAAAAAA==; _gali=searchResultsSearchForm",
        "Host": "www.sahibinden.com",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
    }
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"WARNING: STATUS CODE = {r.status_code}")
    data = r.text.replace("\n", "")
    soup = BeautifulSoup(data)
    infolist = extract_list(soup)
    df = pd.DataFrame(infolist)


def dene1():
    """Extract 1 listings page, given in a saved file, into a DataFrame"""
    with open(localpage, "r") as fin:
        data = fin.read().replace("\n", "")

    soup = BeautifulSoup(data)
    infolist = extract_list(soup)
    df = pd.DataFrame(infolist)
    return df


def dene0():
    with open(localpage, "r") as fin:
        data = fin.read().replace("\n", "")

    soup = BeautifulSoup(data)

    for i, resitem in enumerate(soup.select("tr[class*='searchResultsItem']")):
        # print(i, resitem.get_text())
        # list(resitem.children)
        print("-" * 80)
        for j, td in enumerate(resitem.find_all("td")):
            print(j, ") ", td.get_text().strip())
