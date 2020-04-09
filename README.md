# datasette-lambda

Run [Datasette](https://github.com/simonw/datasette) on AWS API Gateway + AWS Lambda.

## End user use

### Creating

Run `./update-stack <stack-name> <sqlite.db>`, e.g. `./update-stack northwinds northwinds.db`

A CloudFormation stack will be created (or updated) with an S3 bucket.

The stub code and SQLite database will be uploaded to the S3 bucket.

A second CloudFormation stack will then be created (or updated) with the necessary
IAM roles, API Gateway and Lambda entities to expose your Datasette instance
to the web.

### Destroying

Run `./delete-stack <stack-name>` to tear down the infrastructure.

## Maintainer use: Building layer

`./build-datasette-layer <version> <ip>` will SSH to an Amazon Linux 2 server, install the latest Datasette, package it, and publish it as a Lambda layer that contains:

- the most recent version of Datasette and its dependencies
- [Mangum](https://github.com/erm/mangum) and its dependencies, to permit Datasette's ASGI implementation to be exposed to API Gateway requests

This could be made more maintainer-friendly. It currently requires that you:

- know the version of the latest Datasette
- have previously started an Amazon Linux 2 instance

## Known issues / future work

- [ ] Downloads from S3 should use an atomic fetch/rename to be robust against transient errors
- [ ] We should embed the DB in the Lambda package itself, when possible, to avoid the coldstart S3 fetch
- [ ] Repeated calls of update-stack should be robust against template-not-changed errors
- [ ] Fix issue with `base_url` not always being respected in generated URLs (maybe issue in how we use Mangum?)
- [ ] Be able to host multiple DBs
- [ ] Be able to front with a CloudFront distribution
- [ ] Be able to use a custom domain name on CloudFront
- [ ] Be able to use a custom domain name on API Gateway
- [ ] Use the passed-in name of the DB as the DB name
- [ ] Maybe add support into core datasette's `publish` command, fixing [#236](https://github.com/simonw/datasette/issues/236)
