# -*- coding: utf-8 -*-
"""
Created on Thu May 14 14:48:13 2015

@author: nicolai
"""

import requests, re
from bs4 import BeautifulSoup
from multiprocessing import Pool
BASEURL = "http://www.sherdog.com"
fighter_pattern = re.compile("/fighter/")


def get_fighter_page(name):
    name_search = "+".join(name.split(" "))
    search_landing_page = "http://www.sherdog.com/stats/fightfinder?SearchTxt=" + name_search
    
    # Find the fighter page from this
    
    fetched = requests.get(search_landing_page)
    
    name_soup = "/fighter/" + "-".join(name.split(" "))
    
    # find a href element   
    soup = BeautifulSoup(fetched.text)
    
    links = soup.findAll("a", href=re.compile(name_soup))
    
    return BASEURL + links[0]["href"]

    
def find_win_loss(fighter_soup):
    wins_snippet = fighter_soup.find("div", class_ = "bio_graph")
    wins = wins_snippet.find("span", class_="counter")
    wins = [int(x) for x in wins][0]
    # 
    losses_snippet = fighter_soup.find("div", class_ = "bio_graph loser")
    losses = losses_snippet.find("span", class_="counter")
    losses = [int(x) for x in losses][0]
    # 
    return {"wins" : wins, "losses":losses}

def testsoup(page):
    fetched = requests.get(page)
    return BeautifulSoup(fetched.text)
    
def get_opponents(fighter_soup, filter_doubles=True):
    # outbound list
    opponents = []
    # past fights exist as "odd" and "even" rows in a table
    rows_even = fighter_soup.findAll("tr", class_="even")
    rows_odd = fighter_soup.findAll("tr", class_="odd")
    rows = rows_even + rows_odd
    
    # Find opponents and filter doubles
    
    for tr in rows:
        opponent = tr.find("a", href=fighter_pattern)["href"]
        
        # Filter out records of opponents fought multiple times
        if filter_doubles:
            if opponent in opponents:
                continue
            else:
                opponents.append(BASEURL+opponent)
        # If this turns out to be a bad idea
        else:
            opponents.append(BASEURL+opponents)
    # Add baseurl
    return opponents
            
def update_stats(fighter_page):
    fetched = requests.get(fighter_page)
    soup = BeautifulSoup(fetched.text)
    win_loss = find_win_loss(soup)
    # update stats
    wins = win_loss["wins"]
    losses = win_loss["losses"]
    return (wins,losses)
    
def get_combined_record(opponents):
    wins = losses = 0
    stats = get_combined_multiproc(opponents).get(0)
    for tupl in iter(stats):
        wins += tupl[0]
        losses += tupl[1]
    return {"wins" : wins, "losses" : losses}
    
def get_combined_multiproc(opponents):
    pool = Pool(8)
    
    results = pool.map_async(update_stats, opponents)
    pool.close()
    pool.join()
    return results
def main_get_stats(fighter_name):
    page = get_fighter_page(fighter_name)
    fetched = requests.get(page)
    soup = BeautifulSoup(fetched.text)
    # get fighter's win/loss
    win_loss = find_win_loss(soup)
    # find fighter's opponent history
    opponents = get_opponents(soup)
    # Scrape opponents for win_loss
    combined_record = get_combined_record(opponents)
    
    # output
    try:
        ratio = float(win_loss["wins"]) / (win_loss["wins"] + win_loss["losses"])
    except ZeroDivisionError:
        ratio = 1.
    outstr1 = "%s has a win ratio of %f \n" % (fighter_name, ratio)
    outstr2 = "Record: %i wins, %i losses\n" % (win_loss["wins"], win_loss["losses"])
    outstr3 = "Combined opponent history: %i wins and %i losses" % (combined_record["wins"], combined_record["losses"])
    print(outstr1)
    print(outstr2)
    print(outstr3)
