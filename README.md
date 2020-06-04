## name
  list-em-metrics
## version
  0.1
## author
  Julio Leme
## author_email
  julio.balu@gmail.com
## license
  GPLv3+
#3 Description
 List metrics like AWS CLI for Enhanced Monitoring

## About

 This project is a demo, and uses boto3 and click to list metrics from Enhanced Monitoring for a specific RDS DB Instance. Users can list all available metrics (limited by 2000 data points) or chose a specific period.

 I designed this project due to Enhanced Monitoring Graphs limitation for 1 hour period.

## Configuring

 list-em-metrics uses the configuration file created by the AWS cli. e.g.

 'aws configure'

## Required permissions
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds:DescribeDBInstances"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams",
                "logs:GetLogEvents"
            ],
            "Resource": "*"
        }
    ]
}

## Running

 pipenv run python "list-em-metrics.py" --db-instance <instance id> --group <EM metric group> --metrics <metric name>,<metric name>,...,<metric name> --start-time <YYYY-MM-DDTHH:mm:ssZ> --end-time <YYYY-MM-DDTHH:mm:ssZ>

Example:

 pipenv run python list-em-metrics.py --db-instance-identifier sqlserver14se --group disks --metrics usedKb,rdCountPS,rdBytesPS,wrCountPS,wrBytesPS --start-time 2020-05-26T06:00:00Z --end-time 2020-05-26T06:00:20Z


 *--db-instance* is required
 *--group* is required

 Valid groups:

 For SQL Server RDS DB Instances that run on Windows OS:
    cpuUtilization, memory, system, disks, network

 For other DB engines that run on Linux OS:
    cpuUtilization, memory, tasks, diskIO, network, fileSys, loadAverageMinute, swap

 *--metrics* is optional. In case metrics are not provided, all the metrics within the group will be listed

 Valid metris for each group:

 For Windows based OS:
    cpuUtilization: idle, kern, user
    memory        : commitTotKb, commitLimitKb, commitPeakKb, kernTotKb, kernPagedKb, kernNonpagedKb, pageSize, physTotKb, physAvailKb, sqlServerTotKb, sysCacheKb
    system        : handles, threads, processes
    disks         : totalKb, usedKb, usedPc, availKb, availPc, rdCountPS, rdBytesPS, wrCountPS, wrBytesPS
    network       : rdBytesPS, wrBytesPS

For Linux based OS:
    cpuUtilization   : guest, idle, irq, nice, steal, system, total, user, wait
    memory           : active, buffers, cached, dirty, free, hugePagesFree, hugePagesRsvd, hugePagesSize, hugePagesSurp, hugePagesTotal,
                       inactive, mapped, pageTables, slab, total, writeback
    tasks            : blocked, running, sleeping, stopped, total, zombie
    diskIO           : avgQueueLen, avgReqSz, await, diskQueueDepth, readIOsPS, readKb, readKbPS, readLatency, readThroughput, rrqmPS,
                       tps, util, writeIOsPS, writeKb, writeKbPS, writeLatency, writeThroughput, wrqmPS
    network          : rx, tx
    fileSys          : maxFiles, total, used
    loadAverageMinute: fifteen, five, one
    swap             : swap, swap_in, swap_out, free, committed

 *--start-time* is optional. In case start-time is not provided, the metrics within the last hour will be listed, up to 2000 data points.

 *--end-time* is optional. Must be greater than start-time. In case not provided, current time will be considered, but up to 2000 data points will be listed
