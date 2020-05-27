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

available_em_metrics = {
 "Windows" :  {
    "cpuUtilization" : [ "idle" , "kern" , "user" ] ,
    "memory" : [ "commitTotKb" , "commitLimitKb" , "commitPeakKb" , "kernTotKb" , "kernPagedKb" , "kernNonpagedKb" , "pageSize" ,
                 "physTotKb" , "physAvailKb" , "sqlServerTotKb" , "sysCacheKb" ] ,
    "system" : [ "handles" , "threads" , "processes" ] ,
    "disks" : [ "totalKb" , "usedKb" , "usedPc" , "availKb" , "availPc" , "rdCountPS" , "rdBytesPS" , "wrCountPS" , "wrBytesPS" ] ,
    "network" : [ "rdBytesPS" , "wrBytesPS" ] } ,
"Linux" : {
    "cpuUtilization" : [ "guest" , "idle" , "irq" , "nice" , "steal" , "system" , "total" , "user" , "wait" ] ,
    "memory" : [ "active" , "buffers" , "cached" , "dirty" , "free" , "hugePagesFree" , "hugePagesRsvd" , "hugePagesSize" , "hugePagesSurp" , "hugePagesTotal" ,
                 "inactive" , "mapped", "pageTables" , "slab" , "total" , "writeback" ] ,
    "tasks" : [ "blocked" , "running" , "sleeping" , "stopped" , "total" , "zombie" ] ,
    "diskIO" : [ "avgQueueLen" , "avgReqSz" , "await" , "diskQueueDepth" , "readIOsPS" , "readKb" , "readKbPS" , "readLatency" , "readThroughput" , "rrqmPS" ,
                 "tps" , "util" , "writeIOsPS" , "writeKb" , "writeKbPS" , "writeLatency" , "writeThroughput" , "wrqmPS" ] ,
    "network" : [ "rx" , "tx" ] ,
    "fileSys" : [ "maxFiles" , "total" , "used" ] ,
    "loadAverageMinute" : [ "fifteen" , "five" , "one" ] ,
    "swap" : [ "swap" , "swap_in" , "swap_out" , "free" , "committed" ] } }

fixed_em_metrics = { "diskIO" : [ "device" ] ,"fileSys" : [ "mountPoint" , "name" ] ,"network" : [ "interface" ] ,"disks" : [ "name" ] }

def get_resource_id(instance):

    if instance:
        try:
            response = rds.describe_db_instances(DBInstanceIdentifier=instance)
            resource_id = response.get('DBInstances')[0].get('DbiResourceId')
            engine = response.get('DBInstances')[0].get('Engine')
            if engine in [ "sqlserver-ee" , "sqlserver-se" , "sqlserver-ex" , "sqlserver-web" ]:
               so = "Windows"
            else:
               so = "Linux"
        except rds.exceptions.DBInstanceNotFoundFault:
            resource_id = None

    return resource_id, so

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
        start_time = start_time.replace('T', ' ').replace('Z','')
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
        end_time = end_time.replace('T', ' ').replace('Z','')
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

    resource_id, so = get_resource_id(db_instance)

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

        # get the EM metrics group
        metric_group = None
        so_metrics = available_em_metrics.get(so)
        for group in so_metrics:
            if metric in so_metrics.get(group):
                metric_group = group
                break

        if not metric_group:
            print("Metric " + metric + " is not a valid EM metric. Please refer to EM documentation for more information." )
            return

        while iteract <= 2000 and log_timestamp < time_end:
            for event in response.get('events'):
                msg = event.get('message')
                msg_json = json.loads(msg)
                if iteract == 1:
                    data_str = "{ 'engine' : '" + msg_json.get("engine") + "' ,"
                    data_str += " 'instanceID' : '" + db_instance + "' ,"
                    data_str += " 'instanceResourceID' : '" + resource_id + "' ,"
                    data_str += " 'numVCPUs' : " + str(msg_json.get("numVCPUs")) + " ,"
                    data_str += " 'uptime' : '" + msg_json.get("uptime") + "' ,"
                    data_str += " '" + metric_group + "' : ["
                else:
                    data_str += ","
                group = msg_json.get(metric_group)
                data_str += " { 'timestamp' : '" + msg_json.get("timestamp").replace('T', ' ').replace('Z','') + "'"
                if metric_group in [ "network" , "diskIO" , "physicalDeviceIO" , "fileSys" , "disks" ]:
                    for metric_detail in group:
                        fixed_index = 1
                        for fixed_metrics in fixed_em_metrics[metric_group]:
                            if fixed_index == 1:
                                data_str += " , '" + str(metric_detail[fixed_metrics]) + "'"
                                fixed_index = 2
                            else:
                                data_str += " ( '" + str(metric_detail[fixed_metrics]) + "' )"
                        data_str += " : { '" + metric + "': '" + str(metric_detail[metric]) + "' }"
                    data_str += " }"
                else:
                    data_str += " , '" + metric + "' : '" + str(group.get(metric)) + "' }"

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

        #data_str += "\n\t]\n}"
        data_str += " ] }"
        data_str = data_str.replace("'","\"")
        data_json = json.loads(data_str)
        print(data_json)
        #print(data_str)

    return

if __name__ == '__main__':
    list_em_metrics()
