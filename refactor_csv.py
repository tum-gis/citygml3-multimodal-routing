# Script to rearrange the routes evaluation csv file

import csv
import os

# path to the csv file
csv_file = "routes_evaluation.csv"
# path to the new csv file
new_csv_file = "routes_evaluation_new.csv"

# read the csv file
with open(csv_file, 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    # write the new csv file
    with open(new_csv_file, 'w') as new_csv_file:
        csv_writer = csv.writer(new_csv_file, delimiter=',')
        # merge columns route_nr, weight, algorithm to new column called name
        csv_writer.writerow(["route_nr", "weight", "algorithm", "distance", "total_weight", "name"])
        for row in csv_reader:
            # skip the header
            if row[0] == "name":
                continue
            row.append(f"{row[2]}_{row[1]}_{row[0]}")
        
            # write the row to the new csv file
            csv_writer.writerow(row)

print(f"\n\033[92m[INFO] Created new csv file: {os.getcwd()}/{new_csv_file}\033[0m")