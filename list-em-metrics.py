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
@click.option('--startTime', default=None,
    help="The start of the time range to list the metrics. If not provided, only the metrics for the last hour will be returned")
@click.option('--endTime', default=None,
    help="The end of the time range to list the metrics. If not provided, only the metrics for one hour after the start time will be returned")

def list_em_metrics(db_instance, metric, startTime, endTime):

    if startTime:
        start_time = convert_to_timestamp(startTime)
        if not start_time:
            print("Invalid startTime. Please enter startTime formated as YYYY-MM-DD HH:mm:ss")
            return
    else:
        # Get UTC time now
        start_time = datetime.now(timezone.utc)
        # Subtract one hour
        start_time = start_time - timedelta(hours=1)

    if endTime:
        end_time = convert_to_timestamp(endTime)
        if not end_time:
            print("Invalid endTime. Please enter startTime formated as YYYY-MM-DD HH:mm:ss")
            return
    else:
        # Get UTC time now
        end_time = datetime.now(timezone.utc)

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
            response = log.get_log_events(logGroupName="RDSOSMetrics",logStreamName=resource_id,startTime=start_time,endTime=end_time,startFromHead=True)
        except logs.exceptions.ResourceNotFoundException:
            print("Enhanced Monitoriong not enabled for DBInstance " + db_instance)

        iteract = 1
        data_srt = ""
        metric_group = "cpuUtilization" # --> Change This

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
            data_str += "{'timestamp': '" + msg_json.get("timestamp") + "', "
            data_str += "'" + metric + "': " + str(group.get(metric)) + "}"
            iteract += 1

        data_str += "\n\t]\n}"

        print(data_str)

    return

if __name__ == '__main__':
    list_em_metrics()
