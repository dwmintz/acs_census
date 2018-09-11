import csv
import re
import collections as coll
import copy

allcaps = re.compile('^[^a-z]*$')

tables = coll.OrderedDict()


class Table(object):
    def __init__(self, table_id, year, category, name, universe, measure, start_pos):
        self.table_id = table_id
        self.year = year
        self.answers = {}
        self.category = category
        self.name = name
        self.universe = universe
        self.measure = measure
        self.start_pos = start_pos


class Answer(object):
    def __init__(self, number, sequence, position):
        self.number = number
        self.sequence = sequence
        self.position = position
        self.names = {}
        self.levels = {}


def parse_lookup(f, year):
    with open(f, 'rU') as csvfile:
        reader = csv.reader(csvfile)

        # Skip header row
        next(reader)

        for i, row in enumerate(reader):
            if row[3] == "":
                if re.match(allcaps, row[7]):
                    tables[row[1]] = Table(row[1], year, row[8], re.sub(r'\([^)]*\)', '', row[7]), '', '', int(row[4]))
                elif re.match(r'^Universe:.*$', row[7]):
                    tables[row[1]].universe = re.sub(r'Universe:  ', '', row[7]).lower()
            elif re.match(r'^[0-9]*$', row[3]):
                a_num = int(float(row[3]))
                a_pos = str(a_num + tables[row[1]].start_pos - 1)
                tables[row[1]].answers[row[1] + '_' + str(a_num).zfill(3)] = Answer(a_num, row[2], a_pos)
        return


def parse_shells(f):
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
                        lookup_values[str(c + 1)] = ''
                # Set the current level
                cur_level = int(row[5])
                lookup_values[str(row[5])] = row[3]
                try:
                    if row[2] in tables[row[0]].answers:
                        tables[row[0]].answers[row[2]].levels = copy.deepcopy(lookup_values)
                        tables[row[0]].answers[row[2]].levels.pop("a_id")
                except KeyError:
                    pass
    return


def group_answers_by_level(a_dict):
    level_answers = coll.OrderedDict()

    for table_id, val in tables.items():
        for k, v in val.answers.iteritems():
            # Create one dict per table
            if table_id not in level_answers:
                level_answers[table_id] = {}
            for l, value in v.levels.iteritems():
                # Create one set per level, per table
                if l not in level_answers[table_id]:
                    level_answers[table_id][l] = set()
                # Add answers to set
                level_answers[table_id][l].add(value)
    return level_answers


# def id_problem_groupings(level_answers):
#     # For identifying problem groupings
#     # Finds cases where the same answer value appears in the same question
#     # at different levels
#     for k, v in level_answers.iteritems():
#         for l, s in v.iteritems():
#             for i in range(int(l[5]) + 1, len(v) - 1):
#                 if s & v[str(i)] and (s & v[str(i)]) != set([""]):
#                     print k
#                     print s & v[str(i)]
#
#     return


def parse_universes(f):
    with open(f, 'rU') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        dimensions = set()
        universe_dimensions = coll.OrderedDict()
        universe_measure = coll.OrderedDict()

        for i, row in enumerate(reader):
            universe_dimensions[row[0].lower()] = {}
            if row[1] != '':
                universe_measure[row[0].lower()] = row[1]
            for d in range(0, 9, 2):
                dim, val = row[d + 2], row[d + 3]
                if dim != '' and dim != "?":
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
                for c in range(3, 9):
                    level_key = str(c - 2)
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
                                assert not (row[c] == "Family Type" and
                                            clean_answer == "Householder 65 years and over"), \
                                            "Problem in question: %r" % row[0]

        for k, v in u_dims.iteritems():
            for dim, val in v.iteritems():
                dimensions.add(dim)
                if dim not in dimension_values:
                    dimension_values[dim] = set()
                dimension_values[dim].add(val)

        return dimension_values, question_dimensions


def flatten_dimensions(q_dict, all_dims, qs_with_dims, universe_dim, universe_meas):
    for table_id, val in tables.items():
        for k, v in val.answers.iteritems():
            # Set dimension values to "" for all dimensions
            for dim in all_dims:
                v.names[dim] = ""
            # Set the question's measure based on universe
            val.measure = universe_meas[val.universe]

            # Set the dimension values correctly for the universe of the question
            for d, dn in universe_dim[val.universe].iteritems():
                if d in v.names and dn.strip() != '':
                    if v.names[d] == "":
                        v.names[d] = dn
                    else:
                        v.names[d] += '|' + dn

            if v.levels != {}:
                for l, d in v.levels.iteritems():
                    # if a dimension name has been specified for this level of 
                    # the hierarchy on this answer
                    if l in qs_with_dims[table_id]:
                        # Skip values that are blank or Total
                        if clean(d) == "Total" or qs_with_dims[table_id][l] == "":
                            pass
                        # For real values, replace the "" with the clean value name
                        elif qs_with_dims[table_id][l] in v.names and d.strip() != '':
                            if v.names[qs_with_dims[table_id][l]] == "":
                                v.names[qs_with_dims[table_id][l]] = clean(d)
                            else:
                                v.names[qs_with_dims[table_id][l]] += '|' + clean(d)
    return


def clean(dirty):
    cleaned = re.sub('(\:| \(dollars\)| --)', '', dirty).strip()
    return cleaned


def remove_non_leaf_nodes(a_dict):
    tab_by_a = {}
    # Loop through answers by table_id
    for table_id, val in tables.items():
        for a_id, answer in val.answers.iteritems():
            a_vals = set()

            if table_id not in tab_by_a:
                tab_by_a[table_id] = {}

            for d, v in answer.levels.iteritems():
                if clean(v) != '':
                    a_vals.add(clean(v))
            tab_by_a[table_id][a_id] = a_vals

    for k, v in tab_by_a.iteritems():
        for a1, s1 in v.iteritems():
            for a2, s2 in v.iteritems():
                if s1 < s2 and s1 != s2:
                    try:
                        tables[a1.split("_")[0]].answers.pop(a1)
                    except KeyError:
                        pass
    return


def parse():
    for year in range(2009, 2017):
        parse_lookup("input_metadata/ACS" + str(year) + "_5-Yr_Seq_Table_Number_Lookup.txt", year)
        print("Parsed Lookup for %s" % year)
        answers = parse_shells(f='input_metadata/ACS2015_5-Year_TableShells_w_levels.csv')
    q_by_level = group_answers_by_level(answers)
    universe_dim, universe_meas = parse_universes(f='input_metadata/universe_dimensions.csv')

    all_dims, qs_with_dims = see_all_dimensions(f="input_metadata/q_levels_with_dimensions.csv", v_dict=q_by_level,
                                                u_dims=universe_dim)

    remove_non_leaf_nodes(answers)
    flatten_dimensions(tables, all_dims, qs_with_dims, universe_dim, universe_meas)

    return tables, q_by_level
