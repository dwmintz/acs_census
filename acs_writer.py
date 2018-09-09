from acs_parser import parse
import csv
import collections as coll

def output_tables(q_dict, v_dict):
    with open("output_metadata/tables.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(["table_id", "Category", "Universe", "Table Name"])
        for k, row in q_dict.iteritems():
            writer.writerow([row.table_id,
                            row.category,
                            row.universe,
                            row.name])

    with open("output_metadata/answer_dimensions.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        dimension_names = sorted(q_dict["B00001"].answers["B00001_001"].names.keys())
        writer.writerow(["q_id", "a_id", "sequence", "position", "measure"] + dimension_names)


        for table_id, val in q_dict.iteritems():
            for a_id, row in val.answers.iteritems():
                sorted_dims = coll.OrderedDict(sorted(row.names.items()))
                writer.writerow([table_id,
                                a_id,
                                row.sequence,
                                row.position,
                                val.measure] +
                                [v for k, v in sorted_dims.iteritems()])

    with open("output_metadata/answers_eav.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')

        writer.writerow(["q_id", "a_id", "measure", "attribute", "value"])
        for table_id, val in q_dict.iteritems():
            for a_id, row in val.answers.iteritems():
                for a, v in row.names.iteritems():
                    if v <> "":
                        writer.writerow([table_id,
                                        a_id,
                                        val.measure,
                                        a,
                                        v])




    with open("output_metadata/q_levels.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for q, levels in v_dict.iteritems():
            writer.writerow([q, q_dict[q].name])
            writer.writerow([q, "dimensions"])
            writer.writerow([q, "values",
                            list(levels["0"]) if "0" in levels else "",
                            list(levels["1"]) if "1" in levels else "",
                            list(levels["2"]) if "2" in levels else "",
                            list(levels["3"]) if "3" in levels else "",
                            list(levels["4"]) if "4" in levels else "",
                            list(levels["5"]) if "5" in levels else "",
                            list(levels["6"]) if "6" in levels else "",
                            list(levels["7"]) if "7" in levels else ""])

questions, q_by_level = parse()
output_tables(questions, q_by_level)
