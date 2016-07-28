#!/usr/bin/python3
import csv
import random

def gen_tab2_table():
    data = [["day", "month", "year", "ucla", "uci", "ucsf", "ucd", "ucsd"]]
    for year in range(2000, 2017):
        for month in range(1, 13):
            for day in range(1, 32):
                lst = [day, month, year]
                for _ in range(5):
                    lst.append(random.randint(1, 6))
                data.append(lst)
    with open("data/tab_2_data_dates.csv","w") as f: # use "wb" for python2
        writer = csv.writer(f)
        writer.writerows(data)

gen_tab2_table()
