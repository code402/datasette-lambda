# Maintainer's Guide

## Create a new layer (when there are new Datasette releases)

`./build-datasette-layer <version> <ip>` will SSH to an Amazon Linux 2 server, install the latest Datasette, package it, and publish it as a Lambda layer that contains:

- the most recent version of Datasette and its dependencies
- [Mangum](https://github.com/erm/mangum) and its dependencies, to permit Datasette's ASGI implementation to be exposed to API Gateway requests

This could be made more maintainer-friendly. It currently requires that you:

- know the version of the latest Datasette
- have previously started an Amazon Linux 2 instance

## Update the demo

```bash
AWS_PROFILE=code402 ./update-stack datasette-lambda-demo fixtures.db --metadata metadata.json.example --cors --domain datasette-demo.code402.com
```
