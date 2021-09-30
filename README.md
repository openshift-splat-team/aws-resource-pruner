# aws-resource-pruner

## Overview

Automation can sometimes leave stale records in route53.  The intent of this project
is to provide way to detect and clean stale records.

When run, this script will load a snapshot of all the previously existing hosted zones which begin with the name ci-op-.
If the same hosted zones continue to exist, they will be deleted in two phases:

- Delete all non NS and SOA records
- Delete the hosted zone

Since it can take some time for the records to actually be deleted, the script will attempt to delete the hosted zone itself the next time the cronjob runs.

A similar strategy that is implemented to clean up stale hosted zones will check for stale A records in the hosted zone and delete them.

The script will only allow itself to run no more often than every 5 hours to prevent records from being deleted too soon.

Note: This was written for a specific purpose.  Please review the logic to understand if any changes will be needed for a specific use case.

## Requirements

- Create a secret named `aws-route53-credentials` with the content of the desired AWS credentials named `.awscreds`


## Installing

~~~
podman build . --tag your-image-repo/image:latest
podman push your-image-repo/image:latest

oc create -f manifests/context-pvc.yaml
oc create -f manifests/pruning-cronjob.yaml
~~~

