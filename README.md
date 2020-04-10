# datasette-lambda

Run [Datasette](https://github.com/simonw/datasette) on AWS API Gateway + AWS Lambda.

## Getting started

### Creating

Run `./update-stack <stack-name> <sqlite.db>`, e.g. `./update-stack northwinds northwinds.db`

A CloudFormation stack will be created (or updated) with an S3 bucket.

The stub code and SQLite database will be uploaded to the S3 bucket.

A second CloudFormation stack will then be created (or updated) with the necessary
IAM roles, API Gateway and Lambda entities to expose your Datasette instance
to the web.

### Watching logs

`./tail-logs <stack-name>` will watch the CloudWatch logs for the Lambda (NB: not the API Gateway) service - this can be useful for debugging runtime errors in Datasette itself.

### Destroying

Run `./delete-stack <stack-name>` to tear down the infrastructure.

## Known issues / future work

- [x] Downloads from S3 should use an atomic fetch/rename to be robust against transient errors
- [ ] We should embed the DB in the Lambda package itself, when possible, to avoid the coldstart S3 fetch
- [x] Repeated calls of update-stack should be robust against template-not-changed errors
- [x] Fix issue with `base_url` not always being respected in generated URLs (maybe issue in how we use Mangum?)
- [ ] Be able to host multiple DBs
- [ ] Use the passed-in name of the DB as the DB name
- [ ] Create a CloudFront distribution
- [ ] Optionally be able to use a custom domain name on CloudFront

Maybe:

- [ ] Be able to customize the stage name
- [ ] Add support into core datasette's `publish` command, fixing [#236](https://github.com/simonw/datasette/issues/236)
