from acs_parser import parse
import csv
import collections as coll


def output_tables(q_dict, v_dict, td_b_l):
    with open("output_metadata/tables.csv", "w") as csv_file:
        table_set = set()
        for k, row in q_dict.items():
            table_set.add(tuple((row.table_id, row.category, row.universe, row.name, row.measure)))
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(["table_id", "Category", "Universe", "Table Name", "Measure"])
        for row in sorted(table_set):
            writer.writerow(list(row))

    with open("output_metadata/answer_dimensions.csv", "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        dimension_names = sorted(q_dict[tuple(("B01001", 2009))].answers["B01001005"].names.keys())
        writer.writerow(["q_id", "year_id", "a_id", "sequence", "position", "measure"] + dimension_names)

        for table_id, val in q_dict.items():
            for a_id, row in val.answers.items():
                sorted_dims = coll.OrderedDict(sorted(row.names.items()))
                writer.writerow([table_id[0],
                                str(table_id[1]),
                                a_id,
                                row.sequence,
                                row.position,
                                val.measure] +
                                [v for k, v in sorted_dims.items()])

    with open("output_metadata/answers_eav.csv", "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')

        writer.writerow(["q_id", "year", "a_id", "measure", "attribute", "value"])
        for table_id, val in q_dict.items():
            for a_id, row in val.answers.items():
                for a, v in row.names.items():
                    if v != "":
                        writer.writerow([table_id[0],
                                        str(table_id[1]),
                                        a_id,
                                        val.measure,
                                        a,
                                        v])




    with open("output_metadata/q_levels.csv", "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        col_headers = [["Level " + str(i) + " Dimension", "Level " + str(i) + " Values"] for i in range(0, 8)]
        writer.writerow(["Table ID"] + [hed for sublist in col_headers for hed in sublist])
        for table_id, levels in v_dict.items():
            values = []
            for i in range(0, 8):
                try:
                    values.append(td_b_l[table_id][str(i)])
                except KeyError:
                    values.append("")
                values.append(sorted(set(levels[str(i)]) if str(i) in levels else ""))
            writer.writerow([table_id] + values)


questions, q_by_level, table_dimensions_by_level = parse()
output_tables(questions, q_by_level, table_dimensions_by_level)