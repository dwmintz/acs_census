import csv
import re
import collections as coll
import copy
import pandas as pd
import re

allcaps = re.compile('^[^a-z]*$')

q_dict = coll.OrderedDict()
a_dict = coll.OrderedDict()
dict_counter = dict()


def parse_lookup(f):
    with open(f, 'rU') as csvfile:
        reader = csv.reader(csvfile)
        lookup_values = dict()

        # Skip header row
        next(reader)

        for i, row in enumerate(reader):

            if row[3] == "":
                if re.match(allcaps, row[7]):
                    lookup_values['category'] = row[8]
                    lookup_values['q_name'] = re.sub(r'\([^)]*\)', '', row[7])
                    start_pos = int(row[4])
                    lookup_values['q_id'] = row[1]
                elif re.match(r'^Universe:.*$', row[7]):
                    lookup_values['universe'] = re.sub(r'Universe:  ', '', row[7]).lower()
                    q_dict[lookup_values['q_id']] = {
                                                'category': lookup_values['category'],
                                                'universe': lookup_values['universe'],
                                                'name': lookup_values['q_name'] }
            elif re.match(r'^[0-9]*$', row[3]):
                a_num = str(int(float(row[3])))
                a_pos = str(int(float(row[3])) + start_pos - 1)
                a_seq = row[2]
                a_id = row[1] + '_' + a_num.zfill(3)
                a_dict[a_id] = {"position": a_pos,
                                "sequence": a_seq}
        return q_dict, a_dict

def parse_shells(f, a_dict):

    with open(f, 'rU') as csvfile:
        reader = csv.reader(csvfile)
        # Skip header row
        next(reader)
        next(reader)
        
        lookup_values = dict()

        for i, row in enumerate(reader):

            # Skip empty rows and question and universe definitions
            # Reset for each new question
            if row[1] == '':
                lookup_values = dict()
                cur_level = 0
            else:
                lookup_values["a_id"] = row[2]
                # When dropping down a level of hierarchy
                if int(row[5]) < cur_level:
                    # Clear lower levels of hierarchy of their values
                    for c in range(int(row[5]) - 1, cur_level):
                        lookup_values["level" + str(c + 1)] = ''
                
                cur_level = int(row[5])

                # Skip Level 0 Totals
                # if not row[5] == '0' or not row[3][:5] == "Total":
                lookup_values["level" + row[5]] = row[3]

                if row[2] in a_dict:
                    a_dict[row[2]]['levels'] = copy.deepcopy(lookup_values)
                    a_dict[row[2]]['levels'].pop("a_id")
    return a_dict

def group_answers_by_level(a_dict):
    level_answers = coll.OrderedDict()
    

    for k, v in a_dict.iteritems():
        q = k.split("_")[0]
        # Create one dict per question
        if q not in level_answers:
            level_answers[q] = {}
        for l, value in v["levels"].iteritems():
            # Create one set per level, per question
            if l not in level_answers[q]:
                level_answers[q][l] = set()
            # Add answers to set
            level_answers[q][l].add(value)

    # For identifying problem groupings
    # Finds cases where the same answer value appears in the same question
    # at different levels
    for k, v in level_answers.iteritems():
        for l, s in v.iteritems():
            for i in range(int(l[5]) + 1, len(v) - 1):
                if s & v["level" + str(i)] and (s & v["level" + str(i)]) != set([""]):
                    print k
                    print s & v["level" + str(i)]

    return level_answers

def parse_universes(f):
    with open(f, 'rU') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        dimensions = set()
        universe_dimensions = coll.OrderedDict()
        universe_measure = coll.OrderedDict()

        for i, row in enumerate(reader):
            universe_dimensions[row[0].lower()] = {}
            if row[1] <> '':
                universe_measure[row[0]] = row[1]
            for d in range(0, 9, 2):
                dim, val = row[d + 2], row[d + 3]
                if dim <> '' and dim <> "?":
                    dimensions.add(dim)
                    universe_dimensions[row[0].lower()][dim] = val

        # print sorted(dimensions)
        return universe_dimensions, universe_measure


def see_all_dimensions(f, v_dict, u_dims):
    with open(f, 'rU') as csvfile:
        reader = csv.reader(csvfile)
        # Skip header row
        dimensions = set()
        dimension_values = coll.OrderedDict()
        question_dimensions = coll.OrderedDict()

        for i, row in enumerate(reader):
            if row[1] == 'dimensions':
                answers = v_dict[row[0]]
                question_dimensions[row[0]] = {}
                for c in range(3,9):
                    level_key = "level" + str(c-2)
                    # If a dimension name is specified
                    if row[c] != '':
                        # add it to the set of dimensions
                        dimensions.add(row[c])
                        question_dimensions[row[0]][level_key] = row[c]

                        # And then add all values to the dimension's set
                        if row[c] not in dimension_values:
                            dimension_values[row[c]] = set()
                        if level_key in answers and answers[level_key] != '':
                            for a in answers[level_key]:
                                clean_answer = clean(a)
                                dimension_values[row[c]].add(clean_answer)

                                # For finding mislabeled values
                                assert not (row[c] == "Family Type" and clean_answer == "Householder 65 years and over"), "Problem in question: %r" % row[0]
        
        for k, v in u_dims.iteritems():
            for dim, val in v.iteritems():
                dimensions.add(dim)
                if dim not in dimension_values:
                    dimension_values[dim] = set()
                dimension_values[dim].add(val)
        # for k, v in dimension_values.iteritems():
        #     print k
        #     print v

        return dimension_values, question_dimensions

def flatten_dimensions(q_dict, a_dict, all_dims, qs_with_dims, universe_dim, universe_meas):

    for k, v in a_dict.iteritems():
        # Get the question
        q = k.split("_")[0]
        # Get the question's universe
        universe = q_dict[q]["universe"].lower()
        # Set dimension values to "All" for all dimensions
        a_dict[k]["dims"] = {dim:"All" for dim in all_dims}

        # Set the dimension values correctly for the universe of the question
        for d, val in universe_dim[universe].iteritems():
            if d in a_dict[k]["dims"]:
                if a_dict[k]["dims"][d] == "All":
                    a_dict[k]["dims"][d] = val
                else:
                    a_dict[k]["dims"][d] += '|' + val

        if "levels" in v:
            for l, d in v["levels"].iteritems():
                # if a dimension name has been specified for this level of 
                # the hierarchy on this answer
                if l in qs_with_dims[q]:
                    # Skip values that are blank or Total
                    if d == "Total" or qs_with_dims[q][l] == "":
                        pass
                    # For real values, replace the "All" with the clean value name
                    elif qs_with_dims[q][l] in a_dict[k]["dims"]:
                        if a_dict[k]["dims"][qs_with_dims[q][l]] == "All":
                            a_dict[k]["dims"][qs_with_dims[q][l]] = clean(d)
                        else:
                            a_dict[k]["dims"][qs_with_dims[q][l]] += '|' + clean(d)

    return a_dict
    print a_dict["B11001B_005"]["dims"]

def clean(dirty):
    cleaned = re.sub('(\:| \(dollars\)| --)', '', dirty).strip()

    return cleaned


def aggregate_values(row, levels):
    for i in range(0,8):
        if "levels" in row:
            if "level" + str(i) in row["levels"]:
                levels.append(row["levels"]["level" + str(i)])
            else:
                levels.append("")
        else:
            levels = ["", "", "", "", "", "", "", ""]

    return levels


def output_tables(q_dict, a_dict, v_dict):
    with open("questions.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(["q_id", "Category", "Universe", "Question Name"])
        for k, row in q_dict.iteritems():
            writer.writerow([k,
                            row["category"],
                            row["universe"],
                            row["name"]])

    with open("answers.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        dimension_names = sorted(a_dict["B00001_001"]["dims"].keys())
        writer.writerow(["q_id", "a_id", "sequence", "position"] + dimension_names)


        for k, row in a_dict.iteritems():
            # levels = []
            # levels = aggregate_values(row, levels)
            sorted_dims = coll.OrderedDict(sorted(row["dims"].items()))
            writer.writerow([k.split("_")[0],
                            k,
                            row["sequence"],
                            row["position"]] +
                            [v for k, v in sorted_dims.iteritems()])

    with open("q_levels.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for q, levels in v_dict.iteritems():
            writer.writerow([q, q_dict[q]["name"]])
            writer.writerow([q, "dimensions"])
            writer.writerow([q, "values",
                            list(levels["level0"]) if "level0" in levels else "",
                            list(levels["level1"]) if "level1" in levels else "",
                            list(levels["level2"]) if "level2" in levels else "",
                            list(levels["level3"]) if "level3" in levels else "",
                            list(levels["level4"]) if "level4" in levels else "",
                            list(levels["level5"]) if "level5" in levels else "",
                            list(levels["level6"]) if "level6" in levels else "",
                            list(levels["level7"]) if "level7" in levels else ""])



def main():

    questions, answers = parse_lookup(f='ACS_5yr_Seq_Table_Number_Lookup.csv')
    answers = parse_shells(f ='ACS2015_Table_Shells_w_levels.csv', 
                           a_dict = answers)
    q_by_level = group_answers_by_level(answers)
    universe_dim, universe_meas = parse_universes(f = 'universe_dimensions.csv')

    all_dims, qs_with_dims = see_all_dimensions(f="q_levels_with_dimensions.csv", v_dict=q_by_level, u_dims = universe_dim)

    answers_flat = flatten_dimensions(q_dict, a_dict, all_dims, qs_with_dims, universe_dim, universe_meas)

    output_tables(questions, answers_flat, q_by_level)

main()