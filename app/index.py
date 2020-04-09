import json
import datasette
import os
import sqlite3
import glob
import boto3
from mangum import Mangum
from datasette.app import Datasette, DEFAULT_CONFIG, CONFIG_OPTIONS, pm

S3_BUCKET = os.environ['Bucket']
DB_FILE = '/tmp/db.db'

if not os.path.exists(DB_FILE):
    s3 = boto3.client('s3')
    s3.download_file(S3_BUCKET, 'db.db', DB_FILE)

ds = Datasette(
    [DB_FILE], #files,
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

handler = Mangum(app)
