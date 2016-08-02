#!/usr/bin/python3
import csv
import os
import datetime
from os import path
from dateutil import parser
from collections import OrderedDict

input_clinic_order = ["UCD", "UCI", "UCLA", "UCSD", "UCSF"]
output_clinic_order = ["UCLA", "UCI", "UCSF", "UCD", "UCSD"]
slow_query_time = 120 # seconds
slow_query_percentage = 0.5


def transform(filepath, output_filepath):
    line_num = 0 # 1 based
    day_start_line = 0 # 1 based
    with open(filepath, "r") as f:
        reader = csv.reader(f)
        with open(output_filepath, "w") as of:
            writer = csv.writer(of)
            writer.writerow(["day", "month", "year", "ucla", "uci", "ucsf", "ucd", "ucsd"])

            current_date = []
            query_times = []
            current_clinics = dict()
            for row in reader:
                line_num += 1
                if not row[0]:
                    continue
                date = parseDate(row[1])

                # Check if new month
                if current_date != date:
                    if current_date: # don't run on first item
                        output_row = list(current_date)
                        for clinic in output_clinic_order:
                            clinic_data = current_clinics.get(clinic, [])
                            clinic_mark = processClinic(clinic_data, query_times)
                            if not clinic_mark:
                                print("Invalid clinic data\n\tday start line: ", day_start_line, "\n\tcurrent clinics: ", clinic_data)
                            output_row.append(clinic_mark)
                        writer.writerow(output_row)
                        day_start_line = line_num
                        #print(query_times)
                        query_times = []

                        current_clinics = dict()
                    current_date = date

                # Append query time
                query_minutes, query_seconds = int(row[2]), int(row[3])
                query_times.append(query_minutes*60 + query_seconds)

                # Listing every clinic counts separately
                for clinic, ordered_clinic in zip(row[4:], input_clinic_order):
                    if not clinic:
                        if ordered_clinic not in current_clinics:
                            current_clinics[ordered_clinic] = []
                        current_clinics[ordered_clinic].append("")
                        continue
                    elif ":" not in clinic:
                        print("Invalid entry, non empty and no dellimiter: ", row)
                        continue
                    name, count = clinic.split(":")
                    if name != ordered_clinic:
                        print("Invalid clinic order: ", row, " should be ", input_clinic_order)
                    count = int(count)
                    if name not in current_clinics:
                        current_clinics[name] = []
                    current_clinics[name].append(count)
    fixMissingDays(output_filepath)
    return


def fixMissingDays(filepath):
    with open(filepath, "r") as f:
        reader = csv.reader(f)
        with open(filepath + ".tmp", "w") as of:
            writer = csv.writer(of)
            last_date = []
            last_months = 0
            for row in reader:
                if row[0].isalpha():
                    writer.writerow(row)
                    continue
                date = [int(i) for i in row[:3]]
                months = date[1] + date[2] * 12
                if (not last_months or months != last_months) and date[0] != 1:
                    # Start of month missing
                    for missing in range(1, date[0]): # Iterate over missing dates
                        output_row = [missing] + date[1:] + [1 for _ in range(len(output_clinic_order))]
                        writer.writerow(output_row)
                        #print("Missing start: ", output_row)
                elif months == last_months and last_date and date[0] - last_date[0] > 1:
                    # Middle of month missing
                    for missing in range(last_date[0] + 1, date[0]):
                        output_row = [missing] + date[1:] + [1 for _ in range(len(output_clinic_order))]
                        writer.writerow(output_row)
                        #print("Missing middle: ", output_row)
                elif last_months and months - last_months > 0:
                    month_days = (datetime.date(last_date[2], last_date[1] + 1, 1) - datetime.date(last_date[2], last_date[1], 1)).days
                    if last_date[0] != month_days:
                        # Missing end days
                        for missing in range(last_date[0] + 1, month_days + 1):
                            output_row = [missing] + last_date[1:] + [1 for _ in range(len(output_clinic_order))]
                            writer.writerow(output_row)
                            #print("Missing end: ", output_row)

                last_date = date
                last_months = months

                writer.writerow(row)
            # Checking last month for missing days
            month_days = (datetime.date(last_date[2], last_date[1] + 1, 1) - datetime.date(last_date[2], last_date[1], 1)).days
            if last_date[0] != month_days:
                # Missing end days
                for missing in range(last_date[0] + 1, month_days + 1):
                    output_row = [missing] + last_date[1:] + [1 for _ in range(len(output_clinic_order))]
                    writer.writerow(output_row)
                    #print("Missing end: ", output_row)

    os.remove(filepath)
    os.rename(filepath + ".tmp", filepath)


def parseDate(text):
    datetime = parser.parse(text)
    return datetime.day, datetime.month, datetime.year


def processClinic(clinic_data, query_times):
    """ NUMBERS
    if all >0 or not "":
        6
    if some >0 and some 0:
        5
    if some >0 and 0 and -1:
        4
    if some "" or >2min:
        3
    if all "":
        2
    if no data for day, missing day:
        1
    """
    if not clinic_data:
        return  1
    elif clinic_data.count("") == len(clinic_data):
        return 2 # All empty
    elif "" in clinic_data or \
            list(map(lambda x: x > slow_query_time, query_times)).count(True) > (len(query_times) * slow_query_percentage) or \
            all(list(map(lambda x: isinstance(x, int) and x == -1, clinic_data))):
        return 3 # has empty or has 50% slow queries or all are negative
    elif True in list(map(lambda x: x == -1, clinic_data)) and \
            True in list(map(lambda x: x > 0, clinic_data)) or \
            True in list(map(lambda x: x == 0, clinic_data)):
        return 4 # contains all number range negative, positive and maybe zero
    elif True in list(map(lambda x: x == 0, clinic_data)) and \
            True in list(map(lambda x: x > 0, clinic_data)):
        return 5 # mixed >=0
    elif all(map(lambda x: x > 0, clinic_data)):
        return 6 # all >0 and not empty

    """ OLD 4 mark
    elif True in map(lambda x: isinstance(x, int) and x == -1, clinic_data) and \
                True in map(lambda x: isinstance(x, int) and x == 0, clinic_data) and \
                True in map(lambda x: isinstance(x, int) and x > 0, clinic_data):"""
    return None


for file in os.listdir("raw-csv"):
    transform("raw-csv/" + file, "input-csv/" + file)
