import csv
import os.path
import pandas as pd
import concurrent.futures
from acs_parser import tables, parse

parse()

headers = dict()
output_path = "output"
parsed_answers = tables


# Read in template files
for year in [2010]:
    for i in range(1, 123):
        try:
            headers[tuple((year, i))] = pd.read_excel("/Users/Daniel/Downloads/" + str(year) + "_5yr_Summary_FileTemplates/Seq" + str(i) + ".xls", header=None)
        except:
            pass

for key in headers:
    print(key)

# Read in data files


def parse_and_reshape_data(f):

    try:
        pd.read_csv(f)
    except:
        return
        print("File is empty")

    df = pd.read_csv(f, header = None, dtype = {0:"str", 1:"str", 2:"str", 3:"str", 4:"int64", 5:"str"}, low_memory=False)
    logrecno = df[5].tolist()
    file_id = df.iloc[0, 1]
    stusab = df.iloc[1, 2]

    for j in range(6, df.shape[1]):

        dfList = df[j].tolist()

        a_id = headers[tuple((int(file_id[0:4]), int(df.iloc[0, 4])))].iloc[0, j]

        if tuple((a_id[0:6], 2009)) in parsed_answers or tuple((a_id[0:6], 2016)) in parsed_answers:
            q_id = a_id.split("_")[0]


            output = os.path.join(output_path, q_id + ".csv")

            with open(output, "a") as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                for idx, v in enumerate(dfList):
                    if pd.notnull(v):
                        writer.writerow([q_id, file_id, a_id, stusab, logrecno[idx], v])
                    else:
                        pass
        else:
            pass


file_stems = ["/Users/Daniel/Downloads/Tracts_Block_Groups_Only_2010/e20105"]
file_range = range(1, 123)
state_list = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
              "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
              "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
              "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
              "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
files = []

for st in state_list:
    for file in file_range:
        for file_stem in file_stems:
            files.append(file_stem + st.lower() + str(file).zfill(4) + "000.txt")

with concurrent.futures.ProcessPoolExecutor() as executor:
    for i in zip(files, executor.map(parse_and_reshape_data, files)):
        print("Parsed " + str(i))

# for file in files:
#     print("Parsing " + file)
#     parse_and_reshape_data(file)

