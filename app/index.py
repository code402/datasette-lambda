"""Adapter to bootstrap SQLite DB file from S3 bucket if needed, then
   configure Mangum to host the Datasette ASGI app."""
import json
import os
import boto3
from mangum import Mangum
from datasette.app import Datasette, DEFAULT_CONFIG
from datasette.utils import value_as_boolean

S3_BUCKET = os.environ['Bucket']
CORS = os.environ['CORS'] == 'True'
DB_FILES = os.environ['DbFiles'].split('@')
METADATA_PATH = '/var/task/metadata.json'
CONFIG_PATH = '/var/task/config.txt'

def ensure_files():
    """Retrieve the SQLite DB files from S3, if needed.

       Return an array of absolute paths to the DB files this Datasette
       instance should host."""
    files = []

    # The SQLite files are either embedded in the deployment package,
    # or available in the S3 bucket.
    #
    # If they're embedded in the deployment package, they're located
    # at /var/task

    for db_file in DB_FILES:
        abs_path = '/var/task/' + db_file
        if os.path.exists(abs_path):
            files.append(abs_path)

    if files and len(files) != len(DB_FILES):
        # This should never happen.
        raise Exception('some, but not all, dbs were in the deployment package: expected {}; got {}'
                        .format(str(DB_FILES), str(files)))

    if not files:
        for key in DB_FILES:
            db_file = '/tmp/' + key
            db_file_tmp = db_file + '.tmp'

            if not os.path.exists(db_file):
                client = boto3.client('s3')
                client.download_file(S3_BUCKET, key, db_file_tmp)
                os.rename(db_file_tmp, db_file)

            files.append(db_file)

    return files

def load_metadata():
    """Load the metadata.json file, if present."""
    metadata = {}
    if os.path.exists(METADATA_PATH):
        metadata = json.loads(open(METADATA_PATH).read())

    return metadata

def load_config():
    """Load and parse config settings, if present."""
    config = {}
    if os.path.exists(CONFIG_PATH):
        for line in open(CONFIG_PATH):
            if not line:
                continue

            line = line.strip()

            if ':' not in line:
                raise Exception('"{}" should be name:value'.format(line))

            key = line[0:line.find(':')]
            value = line[line.find(':') + 1:]

            # This is a hack; properly we should be introspecting the annotations in cli.py.
            # Still, this works for many of the common settings, so *shrug*.
            if key not in DEFAULT_CONFIG:
                raise Exception('unknown config setting: ' + key)

            default = DEFAULT_CONFIG[key]
            if isinstance(default, bool):
                value = value_as_boolean(value)
            elif isinstance(default, int):
                value = int(value)

            config[key] = value

    return config

def create_handler():
    """Create the Datasette ASGI handler and wrap it in the Mangum adapter."""
    datasette = Datasette(
        files=ensure_files(),
        immutables=[],
        cache_headers=True,
        cors=CORS,
        inspect_data=None,
        metadata=load_metadata(),
        sqlite_extensions=None, #sqlite_extensions,
        template_dir=None, #template_dir,
        plugins_dir=None, #plugins_dir,
        static_mounts=None, #static,
        config=load_config(),
        memory=False, #memory,
        version_note=None #version_note,
    )
    app = datasette.app()
    return Mangum(app)

handler_ = create_handler()

def handler(event, context):
    """Thunk to handle extra stagename from API Gateway."""

    # NB: This code is currently commented out because we're fronting the API Gateway
    #     with a CloudFront distribution. We'll need this code again if we permit
    #     users to specify a custom prefix for the distribution.
    #
    # path doesn't include the stage component, but Datasette requires it in order to
    # correctly construct URLs in some cases.
    #
    # See https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format for description of the format
    # of this object.
    #
    # See https://github.com/simonw/datasette/issues/394#issuecomment-603501719 for where
    # simonw identifies that the full path must be present.

    #event['path'] = '/' + event['requestContext']['stage'] + event['path']
    return handler_(event, context)
