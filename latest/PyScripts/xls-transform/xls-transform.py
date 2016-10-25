#!/usr/bin/python3
import csv
import os
import datetime
from os import path
from dateutil import parser
from collections import OrderedDict

input_clinic_order = ["UCD", "UCI", "UCLA", "UCSD", "UCSF"]
output_clinic_order = ["UCLA", "UCI", "UCSF", "UCD", "UCSD"]
filter_out_hospital_names = True
remove_excess_3_1 = True
reformat_timestamp = True
quoted_indices = []


def read_row(reader):
    for row in reader:
        if len(row) == 14:
            del row[2:7]
            yield row
        elif len(row) == 9:
            yield row
        else:
            print("Invalid column number but will try to process it")


def transform(filepath, output_filepath):
    """
    Transforms "./queries/anemiaMedsICD9_10.txt,Fri Sep  9 11:30:01 PDT 2016,UCSD:-1,UCD:25,UCI:-1,UCSF:-1,UCLA:-1,3,1,UCD:25,UCI:-1,UCLA:-1,UCSD:-1,UCSF:-1"
    into "./queries/anemiaMedsICD9_10.txt,Fri Sep  9 11:30:01 PDT 2016,3,1,UCD:25,UCI:-1,UCLA:-1,UCSD:-1,UCSF:-1"
    Removes the first set of clinics
    :param filepath:
    :param output_filepath:
    :return:
    """
    with open(filepath, "r") as f:
        reader = csv.reader(f)
        with open(output_filepath, "w") as of:
            writer = csv.writer(of)
            for row in read_row(reader):
                for i in quoted_indices:
                    row[i] = "'%s'" % (row[i],)
                if filter_out_hospital_names:
                    for i in range(4, len(row)):
                        if ":" in row[i]:
                            row[i] = row[i][row[i].index(":")+1:]
                if remove_excess_3_1:
                    del row[2:4]
                if reformat_timestamp and row[1]:
                    dt = parser.parse(row[1])
                    dt = dt.isoformat()
                    row[1] = dt
                writer.writerow(row)


for file in os.listdir("input"):
    transform("input/" + file, "output/" + file)
