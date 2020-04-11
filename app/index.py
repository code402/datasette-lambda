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
PREFIX = os.environ['Prefix']

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


    if PREFIX:
        config['base_url'] = '/{}/'.format(PREFIX)
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

    # Path handling is a little curious.
    #
    # (1) user sends request in CloudFront to /some/path
    # (2) CloudFront forwards to API Gateway with a prefix, resulting API Gateway
    #     seeing /datasette/some/path
    # (3) API Gateway forwards to Lambda with stageName = datasette and path = /some/path
    #
    # In the case where there is no base_url, things just work.
    #
    # In the other case, we need to do a little work.
    # This is because API Gateway is the default cache behavior, so it sees all requests,
    # including ones that don't have the base url.
    ok = not PREFIX or event['path'].startswith('/{}/'.format(PREFIX))

    if ok:
        return handler_(event, context)

    return {
        "isBase64Encoded": False,
        "statusCode": 404,
        "headers": {},
        "multiValueHeaders": {},
        "body": "Not found"
    }
