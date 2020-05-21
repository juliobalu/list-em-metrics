import boto3
import botocore
import click
import json
from datetime import datetime
from datetime import timezone
from datetime import timedelta

session = boto3.Session()
rds = session.client('rds')
log = session.client('logs')

def get_resource_id(instance):

    if instance:
        try:
            resource_id = rds.describe_db_instances(DBInstanceIdentifier=instance)['DBInstances'][0]['DbiResourceId']
        except rds.exceptions.DBInstanceNotFoundFault:
            resource_id = None

    return resource_id

def convert_to_timestamp(date_time):

    try:
        date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        date_time = None
        return date_time

    date_time = date_time.replace(tzinfo=timezone.utc)
    date_time = datetime.timestamp(date_time)

    return date_time

@click.command()
@click.option('--db-instance', default=None,
    help="Only metrics for a DBInstance")
@click.option('--metric', default=None,
    help="Listing only one metric at a time")
@click.option('--start-time', default=None,
    help="The start of the time range to list the metrics. If not provided, only the metrics for the last hour will be returned")
@click.option('--end-time', default=None,
    help="The end of the time range to list the metrics. If not provided, only the metrics for one hour after the start time will be returned")

def list_em_metrics(db_instance, metric, start_time, end_time):

    if start_time:
        time_start = convert_to_timestamp(start_time)
        if not time_start:
            print("Invalid startTime. Please enter startTime formated as YYYY-MM-DD HH:mm:ss")
            return
    else:
        # Get UTC time now
        time_start = datetime.now(timezone.utc)
        # Subtract one hour
        time_start = time_start - timedelta(hours=1)
        time_start = datetime.timestamp(time_start)

    if end_time:
        time_end = convert_to_timestamp(end_time)
        if not time_end:
            print("Invalid endTime. Please enter startTime formated as YYYY-MM-DD HH:mm:ss")
            return
    else:
        # Get UTC time now
        time_end = datetime.now(timezone.utc)
        time_end = datetime.timestamp(time_end)

    if time_end <= time_start:
        if not start_time:
            print("Error: start-time was not provided. start-time considered as " + datetime.utcfromtimestamp(time_start).strftime("%Y-%m-%d %H:%M:%S") + ". end-time must be greater than start-time.")
        else:
            print("Error: end-time must be greater than start-time")
        return

    if not db_instance:
        print("Please specify a DBInstance Identifier to list the metrics.")
        return

    if not metric:
        print("Please specify a metric. Type list-em-metrics --metric --help for a list of available options.")
        return

    resource_id = get_resource_id(db_instance)

    if not resource_id:
        print("DBInstance not found. Please review the DbInstance Identifier and try again.")
    else:
        #print("Resource id: " + resource_id)

        try:
            response = log.get_log_events(logGroupName="RDSOSMetrics",logStreamName=resource_id,startTime=int(time_start*1000),endTime=int(time_end*1000),startFromHead=True)
        except log.exceptions.ResourceNotFoundException:
            print("Enhanced Monitoriong not enabled for DBInstance " + db_instance)

        iteract = 1
        data_str = ""
        log_timestamp = time_start
        metric_group = "cpuUtilization" # --> Change This

        while iteract <= 2000 and log_timestamp < time_end:
            for event in response.get('events'):
                msg = event.get('message')
                msg_json = json.loads(msg)
                if iteract == 1:
                    data_str = "{\n\t'engine': '" + msg_json.get("engine") + "',\n\t"
                    data_str += "'instanceID': '" + db_instance + "',\n\t"
                    data_str += "'instanceResourceID': '" + resource_id + "',\n\t"
                    data_str += "'numVCPUs': " + str(msg_json.get("numVCPUs")) + ",\n\t"
                    data_str += "'" + metric_group + "': [\n\t\t"
                else:
                    data_str += ",\n\t\t"
                group = msg_json.get(metric_group)
                data_str += "{'timestamp': '" + msg_json.get("timestamp").replace('T', ' ').replace('Z','') + "', "
                data_str += "'" + metric + "': " + str(group.get(metric)) + "}"

                log_timestamp = msg_json.get("timestamp")
                log_timestamp = log_timestamp.replace('T', ' ').replace('Z','')
                log_timestamp = convert_to_timestamp(log_timestamp)

                iteract += 1
                if iteract > 2000:
                    break

            next_token = response.get('nextForwardToken')

            response = log.get_log_events(logGroupName="RDSOSMetrics",logStreamName=resource_id,startTime=int(time_start*1000),endTime=int(time_end*1000),nextToken=next_token,startFromHead=True)
            if next_token == response.get('nextForwardToken'):
                break

        data_str += "\n\t]\n}"

        print(data_str)

    return

if __name__ == '__main__':
    list_em_metrics()
