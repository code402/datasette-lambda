import json
import datasette
import os
import sqlite3
import glob
import boto3
from mangum import Mangum
from datasette.app import Datasette, DEFAULT_CONFIG, CONFIG_OPTIONS, pm

S3_BUCKET = os.environ['Bucket']
DB_FILES = os.environ['DbFiles'].split('@')

files = []

# The SQLite files are either embedded in the deployment package,
# or available in the S3 bucket.
#
# If they're embedded in the deployment package, they're located
# at /var/task

for file in DB_FILES:
    abs_path = '/var/task/' + file
    if os.path.exists(abs_path):
        files.append(abs_path)

if files and len(files) != len(DB_FILES):
    # This should never happen.
    raise Exception('some, but not all, dbs were in the deployment package: expected ' + str(DB_FILES) + '; got ' + str(files))

if not files:
    for file in DB_FILES:
        db_file = '/tmp/' + file
        db_file_tmp = db_file + '.tmp'

        if not os.path.exists(db_file):
            s3 = boto3.client('s3')
            s3.download_file(S3_BUCKET, file, db_file_tmp)
            os.rename(db_file_tmp, db_file)

        files.append(file)

ds = Datasette(
    files,
    immutables=[],
    cache_headers=True,
    cors=True,
    inspect_data=None,
    metadata=None, #metadata_data,
    sqlite_extensions=None, #sqlite_extensions,
    template_dir=None, #template_dir,
    plugins_dir=None, #plugins_dir,
    static_mounts=None, #static,
    config={
        'base_url': '/datasette/'
    }, #dict(config),
    memory=False, #memory,
    version_note=None #version_note,
)
app = ds.app()
handler_ = Mangum(app)

def handler(event, context):
    # path doesn't include the stage component, but Datasette requires it in order to
    # correctly construct URLs in some cases.
    #
    # See https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format for description of the format
    # of this object.
    #
    # See https://github.com/simonw/datasette/issues/394#issuecomment-603501719 for where
    # simonw identifies that the full path must be present.

    event['path'] = '/' + event['requestContext']['stage'] + event['path']
    return handler_(event, context)

