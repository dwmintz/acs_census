import csv
import re
import collections as coll
import copy
import os.path
import ast
import shutil

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


class Universe(object):
    def __init__(self, name, dimensions):
        self.name = name
        self.dimensions = dimensions


def clear_output_folders():
    shutil.rmtree("output_metadata/")
    os.mkdir("output_metadata/")
    shutil.rmtree("output/")
    os.mkdir("output/")

def parse_lookup(f, year):
    with open(f, 'r') as csvfile:
        reader = csv.reader(csvfile)

        # Skip header row
        next(reader)

        to_exclude = set()

        for i, row in enumerate(reader):
            if row[1] in to_exclude:
                continue
            if row[3].strip() == "" or row[3] == ".":
                if row[8].strip() in ["Imputation", "Quality Measures", "Imputations"]:
                    to_exclude.add(row[1])
                    continue
                elif re.match(allcaps, row[7]):
                    tables[tuple((row[1], year))] = Table(row[1], year, row[8], clean(re.sub(r'\([^)]*\)', '', row[7])), '', '', int(row[4]))
                elif re.match(r'^Universe:.*$', row[7]):
                    tables[tuple((row[1], year))].universe = re.sub(r'Universe:', '', row[7]).lower().strip()
            elif re.match(r'^[0-9]*$', row[3]):
                a_num = int(float(row[3]))
                a_pos = str(a_num + tables[tuple((row[1], year))].start_pos - 1)
                tables[tuple((row[1], year))].answers[row[1] + str(a_num).zfill(3)] = Answer(a_num, row[2], a_pos)

    return to_exclude


def read_in_table_definitions(f, year):
    with open(f, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for i, row in enumerate(reader):
            try:
                tables[tuple((row[0], year))].measure = row[4]
            except KeyError:
                pass

def add_levels_to_shells(shells, tables_to_skip):
    parsed_shells = coll.OrderedDict()
    # years = set(year[0] for year in shells)
    # Parse all shells then compare tables without levels to those with and look for exact matches
    # Then write all shells back out
    for shell in shells:
        with open(shell[1], 'r') as csvfile:
            year = shell[0]
            reader = csv.reader(csvfile)
            # Skip header row
            next(reader)

            for i, row in enumerate(reader):
                if row[0] not in tables_to_skip:
                    table_id = row[0]
                    answer_id = row[2].replace("_", "")
                    # Skip empty rows and question and universe definitions
                    # Reset for each new question
                    if table_id not in parsed_shells:
                        parsed_shells[table_id] = {}
                    if year not in parsed_shells[table_id]:
                        parsed_shells[table_id][year] = {}
                        # Assume levels are complete for that table/year
                        parsed_shells[table_id][year].update({"level_status": "complete",
                                                              "values": coll.OrderedDict(),
                                                              "levels": coll.OrderedDict()})

                    if row[2].strip() != '':
                        parsed_shells[table_id][year]["values"][answer_id] = row[3]
                        # If any of the levels aren't set, mark the whole table/year as incomplete
                        try:
                            if clean(row[5]) == "":
                                parsed_shells[table_id][year]["level_status"] = "incomplete"
                            else:
                                parsed_shells[table_id][year]["levels"][answer_id] = clean(row[5])
                        except IndexError:
                            parsed_shells[table_id][year]["level_status"] = "incomplete"

    # Use shells with levels to complete shells without levels
    for table_id, table in parsed_shells.items():
        for outer_year, outer_content in table.items():
            if outer_content["level_status"] == "complete":
                continue
            # Zero in on years that need completion
            elif outer_content["level_status"] == "incomplete":
                for inner_year, inner_content in table.items():
                    # Check to see if all the values match another year's values
                    if inner_year != outer_year and inner_content["level_status"] == "complete" \
                            and outer_content["values"] == inner_content["values"]:
                        # If so, set their levels to match
                        outer_content["levels"] = copy.deepcopy(inner_content["levels"])
                        outer_content["level_status"] = "complete"
                        print(table_id + " from " + str(outer_year) + " matched " + str(inner_year))
                        break

    for table_id, table in parsed_shells.items():
        for year, data in table.items():
            with open("output_metadata/ACS" + str(year) + "_shell_w_levels.csv", 'a') as csvfile:
                writer = csv.writer(csvfile)
                i = 1
                for answer_id, value in data["values"].items():
                    try:
                        writer.writerow([table_id, str(i), answer_id, value, '', data["levels"][answer_id]])
                    except KeyError:
                        writer.writerow([table_id, str(i), answer_id, value, '', ''])
                    i += 1


def construct_hierarchies(f, year, to_exclude):
    with open(f, 'r') as csvfile:
        reader = csv.reader(csvfile)
        missing_levels = set()

        lookup_values = dict()
        last_row_table_id, cur_level = "", 0

        for i, row in enumerate(reader):
            if row[0] in to_exclude:
                break

            try:
                int(row[5])
            except ValueError:
                missing_levels.add(tuple((str(year), row[0], row[2], row[3])))
                continue
            # Skip empty rows and question and universe definitions
            # Reset for each new question
            if row[0] != last_row_table_id:
                lookup_values = dict()
                cur_level = 0

            lookup_values["a_id"] = row[2].replace('_', '')
            # When dropping down a level of hierarchy
            if int(row[5]) < cur_level:
                # Clear lower levels of hierarchy of their values
                for c in range(int(row[5]) - 1, cur_level):
                    lookup_values[str(c + 1)] = ''
            # Set the current level
            cur_level = int(row[5])
            lookup_values[str(row[5])] = row[3]
            try:
                if row[2].replace('_', '') in tables[tuple((row[0], year))].answers:
                    tables[tuple((row[0], year))].answers[row[2]].levels = copy.deepcopy(lookup_values)
                    tables[tuple((row[0], year))].answers[row[2]].levels.pop("a_id")
            except KeyError:
                pass
            last_row_table_id = row[0]

        if len(missing_levels) > 0:
            print("You're missing levels for the following values: " + "\n".join([",".join(t) for t in missing_levels]))
            exit("Add those levels before continuing")
    return


def id_problem_groupings(level_answers):
    # For identifying problem groupings
    # Finds cases where the same answer value appears in the same question
    # at different levels
    for table_id, v in level_answers.items():
        for l, s in v.items():
            for i in range(int(l) + 1, len(v) - 1):
                # print(s)
                # print(v[str(i)])
                try:
                    if len(s & v[str(i)]) > 0 and s & v[str(i)] != {''}:
                        print(table_id)
                        print(l)
                        print(s & v[str(i)])
                except KeyError:
                    pass
    return


def unify_years():
    universes, table_ids = set(), set()
    table_level_answers = coll.OrderedDict()

    # Iterate through all tables from all years parsed
    for t_id_year, table in tables.items():
        # Build up sets of table universes and table_ids
        universes.add(table.universe)
        table_ids.add(table.table_id)

        if table.table_id not in table_level_answers:
            table_level_answers[table.table_id] = {}

        for k, v in table.answers.items():
            for l, value in v.levels.items():
                # Create one set of answer values per level, per table
                if l not in table_level_answers[table.table_id]:
                    table_level_answers[table.table_id][l] = set()
                # Add answer value to set
                table_level_answers[table.table_id][l].add(clean(value))

    return universes, table_ids, table_level_answers


def output_all_universes(f, universes):
    csv_unis = dict()

    # Read in universe dimensions that are already in the csv
    with open('input_metadata/universe_dimensions.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)

        # Skip header row
        next(reader)

        # Add each universe and its parsed dimensions
        for i, row in enumerate(reader):
            # First grab universes in the CSV that have a dimensions set
            try:
                csv_unis[row[0]] = Universe(row[0].lower(), {})
                for col in row[2:]:
                    if col != '':
                        csv_unis[row[0]].dimensions.update(ast.literal_eval(col))
            except IndexError:
                # If a universe doesn't have dimensions, just add its universe name
                csv_unis[row[0]] = Universe(row[0].lower(), [])

    # Write back out the universes to CSV, but include ones that were newly parsed
    with open(f, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["universe", "dimensions"])
        for uni_name, uni in csv_unis.items():
            writer.writerow([uni.name] +
                             [{dim: value} for dim, value in uni.dimensions.items() if dim.strip() != ''])

            # Match universes that were in the CSV with those parsed from Table Shells
            try:
                universes.remove(uni.name.lower())
            except KeyError:
                print("Could not remove " + uni.name.lower())

        for uni in universes:
            writer.writerow([uni.lower()])

    # Return the dictionary of universes for use downstream
    return csv_unis


def see_all_dimensions(f, v_dict, u_dims):
    with open(f, 'r') as csvfile:
        reader = csv.reader(csvfile)
        # Skip header row
        next(reader)

        dimensions = set()
        dimension_values = coll.OrderedDict()
        question_dimensions = coll.OrderedDict()

        for i, row in enumerate(reader):
            try:
                answers = v_dict[row[0]]
            except KeyError:
                answers = {}
            question_dimensions[row[0]] = {}
            for c in range(1, 16, 2):
                level_key = str(int((c - 1)/2))
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

        for k, v in u_dims.items():
            for dim, value in v.dimensions.items():
                dimensions.add(dim)
                if dim not in dimension_values:
                    dimension_values[dim] = set()
                dimension_values[dim].add(value)

        return dimension_values, question_dimensions


def flatten_dimensions(all_dims, qs_with_dims, universes):
    for table_id, val in tables.items():
        for k, v in val.answers.items():
            # Set dimension values to "" for all dimensions
            for dim in all_dims:
                v.names[dim] = ""

            # Set the dimension values correctly for the universe of the question

            for d, dn in universes[val.universe.strip()].dimensions.items():
                try:
                    if d in v.names and dn.strip() != '':
                        if v.names[d] == "":
                            v.names[d] = dn
                        else:
                            v.names[d] += '|' + dn
                except:
                    v.names[d] = "Failed"

            if v.levels != {}:
                for l, d in v.levels.items():
                    # if a dimension name has been specified for this level of
                    # the hierarchy on this answer
                    try:
                        if l in qs_with_dims[table_id[0]]:
                            # Skip values that are blank or Total
                            if clean(d) == "Total" or qs_with_dims[table_id[0]][l] == "":
                                pass
                            # For real values, replace the "" with the clean value name
                            elif qs_with_dims[table_id[0]][l] in v.names and d.strip() != '':
                                if v.names[qs_with_dims[table_id[0]][l]] == "":
                                    v.names[qs_with_dims[table_id[0]][l]] = clean(d)
                                else:
                                    v.names[qs_with_dims[table_id[0]][l]] += '|' + clean(d)
                            else:
                                pass
                    except KeyError:
                        "Missing"
    return

# Helper function
def clean(dirty):
    cleaned = re.sub('(\:| \(dollars\)| --)', '', dirty).strip()
    return cleaned


def remove_non_leaf_nodes(a_dict):
    tab_by_a = {}
    # Loop through answers by table_id
    for table_id, val in tables.items():
        for a_id, answer in val.answers.items():
            a_vals = set()

            if table_id not in tab_by_a:
                tab_by_a[table_id] = {}

            for d, v in answer.levels.items():
                if clean(v) != '':
                    a_vals.add(clean(v))
            tab_by_a[table_id][a_id] = a_vals

    for k, v in tab_by_a.items():
        for a1, s1 in v.items():
            for a2, s2 in v.items():
                if s1 < s2 and s1 != s2:
                    try:
                        tables[k].answers.pop(a1)
                        print("Removed " + a1)
                    except KeyError:
                        pass
    return


def parse():
    clear_output_folders()
    years = [2009, 2010, 2015, 2016]
    shell_paths = []
    excluded_tables = set()

    for year in years:
        excluded_tables |= parse_lookup("input_metadata/ACS" + str(year) + "_5-Yr_Seq_Table_Number_Lookup.txt", year)
        print("Parsed Lookup for %s" % year)

        if os.path.isfile("input_metadata/ACS" + str(year) + "_shell_w_levels.csv"):
            shell_paths.append(tuple((year, "input_metadata/ACS" + str(year) + "_shell_w_levels.csv")))
        else:
            shell_paths.append(tuple((year, "input_metadata/ACS" + str(year) + "_5-Year_TableShells.csv")))

        read_in_table_definitions("input_metadata/tables.csv", year)

    add_levels_to_shells(shell_paths, excluded_tables)

    for year in years:
        answers = construct_hierarchies("output_metadata/ACS" + str(year) + "_shell_w_levels.csv", year, excluded_tables)
        print("Parsed Shell for %s" % year)
    print(excluded_tables)
    universes, table_ids, table_level_answers = unify_years()
    universes = output_all_universes('output_metadata/universe_dimensions.csv', universes)

    all_dims, qs_with_dims = see_all_dimensions(f="input_metadata/q_levels.csv", v_dict=table_level_answers,
                                                u_dims=universes)
    id_problem_groupings(table_level_answers)

    remove_non_leaf_nodes(answers)
    flatten_dimensions(all_dims, qs_with_dims, universes)

    return tables, table_level_answers, qs_with_dims

# parse()