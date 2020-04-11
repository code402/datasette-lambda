# datasette-lambda

Run [Datasette](https://github.com/simonw/datasette) on AWS as a serverless application:

<div><a href='//sketchviz.com/@cldellow/81af2bc7bec979e5725f0718e752ac47'><img src='https://sketchviz.com/@cldellow/81af2bc7bec979e5725f0718e752ac47/c8d9beceb2a727d2299c682c7ba8c276f702b8dd.sketchy.png' style='max-width: 100%;'></a></div>

Sufficiently small databases (unzipped size up to ~250 MB, zipped size up to ~50 MB) will be inlined in the Lambda deployment package. Others will be published to S3 and fetched on Lambda startup.

You can see a demo using Datasette's fixtures db here: https://datasette-demo.code402.com/

## Getting started

### Creating

Clone the repo and run `./update-stack <stack-name> [flags] <sqlite.db> [<sqlite.db> ...]`, e.g.:

```bash
git clone https://github.com/code402/datasette-lambda.git
cd datasette-lambda
./update-stack northwinds northwinds.db`
```

Some Datasette flags are supported:

- `--config key:value`, to set [config options](https://datasette.readthedocs.io/en/stable/config.html)
- `--cors`, to enable `Access-Control-Allow-Origin: *` headers on responses
- `--metadata <metadata.json>`, to provide [metadata](https://datasette.readthedocs.io/en/stable/metadata.html)

And some non-Datasette flags are supported:

- `--domain example.com` or `--domain subdomain.example.com`, if `example.com` is a hosted zone in Route 53
  - register a `CNAME` record that points to the CloudFront distribution
  - register an SSL certificate for the domain (you'll have to ack a confirmation email from Amazon)
  - associate that certificate to the CloudFront distribution
- `--prefix some/path`, to mount the Datasette app at a path other than the root

A CloudFormation stack will be created (or updated) with an S3 bucket.

The stub code and SQLite database(s) will be uploaded to the S3 bucket.

A second CloudFormation stack will then be created (or updated) with the necessary
IAM roles, CloudFront, API Gateway and Lambda entities to expose your Datasette
instance to the web.

### Watching logs

`./tail-logs <stack-name>` will watch the CloudWatch logs for the Lambda (NB: not the API Gateway) service - this can be useful for debugging runtime errors in Datasette itself.

### Destroying

Run `./delete-stack <stack-name>` to tear down the infrastructure.

## Known issues / future work

- [x] Downloads from S3 should use an atomic fetch/rename to be robust against transient errors
- [x] We should embed the DB in the Lambda package itself, when possible, to avoid the coldstart S3 fetch
- [x] Repeated calls of update-stack should be robust against template-not-changed errors
- [x] Fix issue with `base_url` not always being respected in generated URLs (maybe issue in how we use Mangum?)
- [x] Be able to host multiple DBs
- [x] Use the passed-in name of the DB as the DB name
- [x] Create a CloudFront distribution
- [x] Optionally be able to use a custom domain name on CloudFront
- [x] Parity: Support CORS flag
- [x] Parity: Support metadata flag
- [x] Parity: Support config options
- [ ] Use API Gateway's faster/cheaper HTTP APIs instead of REST APIs (requires [erm/mangum #94](https://github.com/erm/mangum/pull/94))

Maybe:

- [x] Be able to customize the "mount" point of the CloudFront distribution
- [ ] Add support into core datasette's `publish` command, fixing [#236](https://github.com/simonw/datasette/issues/236)
