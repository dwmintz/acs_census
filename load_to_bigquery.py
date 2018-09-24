#
# from google.cloud import bigquery
# client = bigquery.Client()
# dataset_id = 'american_community_explorer'
#
# dataset_ref = client.dataset(dataset_id)
# job_config = bigquery.LoadJobConfig()
# job_config.schema = [
#     bigquery.SchemaField('table_id', 'STRING'),
#     bigquery.SchemaField('file_id', 'STRING'),
#     bigquery.SchemaField('answer_id', 'STRING'),
#     bigquery.SchemaField('stusab', 'STRING'),
#     bigquery.SchemaField('logrecno', 'STRING'),
#     bigquery.SchemaField('value', 'FLOAT')
# ]
# # job_config.skip_leading_rows = 1
# # The source format defaults to CSV, so the line below is optional.
# job_config.source_format = bigquery.SourceFormat.CSV
#
# uri = 'gs://acs_5yr_2016/tracts_and_bgs/B00002.csv.gz'
#
#
# load_job = client.load_table_from_uri(
#     uri,
#     dataset_ref.table('acs_data_B00002'),
#     job_config=job_config)  # API request
#
# assert load_job.job_type == 'load'
#
# load_job.result()  # Waits for table load to complete.
#
# assert load_job.state == 'DONE'


import subprocess
from acs_parser import parse

def main():
    tables, trash1, trash2 = parse()

    for k, v in tables.items():
        if k[1] == 2016:
            subprocess.call(['bq load --source_format=CSV '
                            'american_community_explorer.acs_data_' + v.table_id +
                            ' gs://acs_5yr_2016/tracts_and_bgs/' + v.table_id + '.csv.gz '
                             'table_id:STRING,file_id:STRING,answer_id:STRING,stusab:STRING,logrecno:STRING,value:FLOAT'],
                            shell=True)
        else:
            pass

main()
