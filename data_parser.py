import csv
import os.path
import pandas as pd
from numbers import Number
import concurrent.futures
from acs_parser import a_dict

headers = []
output_path = "/Users/Daniel/Documents/Work/Looker/github_repositories/acs_census/output"
parsed_answers = a_dict

# Read in template files
for i in range(1, 123):
    headers.append(pd.read_excel( "/Users/Daniel/Downloads/templates 3/Seq" + str(i) + ".xls" , header = None))

# Read in data files

def parse_and_reshape_data(f):
    df = pd.read_csv(f, header = None, dtype = {0:"string", 1:"string", 2:"string", 3:"string", 4:"int64", 5:"string"}, low_memory = False)
    logrecno = df[5].tolist()
    file_id = df.iloc[0, 1]
    stusab = df.iloc[1, 2]

    for j in range(6, df.shape[1]):
        
        dfList = df[j].tolist()

        a_id = headers[df.iloc[0, 4] - 1].iloc[0, j]
        if a_id in parsed_answers:
            q_id = a_id.split("_")[0]
            

            output = os.path.join(output_path, q_id + ".csv")

            with open(output, "a") as csv_file:
                writer = csv.writer(csv_file, delimiter=',' )
                for idx, v in enumerate(dfList):
                    if pd.notnull(v):
                        writer.writerow([q_id, file_id, a_id, stusab, logrecno[idx], v])
                    else:
                        pass
        else:
            pass

file_stem = "/Users/Daniel/Downloads/data/tab4/sumfile/prod/2012thru2016/group2/e20165"
file_range = range(1, 123)
state_list = ['ak', 'al', 'ar', 'az']
files = []

for st in state_list:
    for file in file_range:
        files.append(file_stem + st + str(file).zfill(4) + "000.txt")

with concurrent.futures.ProcessPoolExecutor() as executor:
    for i in zip(files, executor.map(parse_and_reshape_data, files)):
        print "Parsed " + str(i)
