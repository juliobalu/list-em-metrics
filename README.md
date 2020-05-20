# list-em-metrics
 List metics like AWS CLI for Enhanced Monitoring

## About

 This project is a demo, and uses boto3 and click to list metrics from Enhanced Monitoring for a specific RDS DB Instance. Users can list all available metrics (limited by 2000 data points) or chose a specific period.

 I designed this project deu to Enhanced Monitoring Graphs limitation for 1 hour period.

## Configuring

 list-em-metrics uses the configuration file created by the AWS cli. e.g.

 `aws configure --profile <profile_name>`

## Required permissions



## Running

 pipenv run python "list-em-metrics.py" --db-instance=<instance id> --metric=<metric name> <--start-time=YYYY-MM-DD HH:mm:ss> <--end-time=YYYY-MM-DD HH:mm:ss>

 *db-instance* is required
 *--metric* is required. Valid names are

 *--start-time* is optional
 *--end-time* is optional
