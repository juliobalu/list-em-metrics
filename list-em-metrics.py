import boto3
import botocore
import click

session = boto3.Session()
rds = session.client('rds')

def get_resource_id(instance):
    resourceid = None

    resourceid = rds.describe_db_instances(DBInstanceIdentifier=instance)['DBInstances'][0]['DbiResourceId']

    return resourceid

@click.option('--db-instance', default=None,
    help="Only metrics for a DBInstance")

@click.group()
def cli():
    """list-em-metrics retunrs Enhanced Monitoring metrics"""

    resource_id = get_resource_id(instance)

    if resourceid:
        print("Resource id: " + resource_id)
    else:
        print("DBInstance not found. Please check the DBInstance Identifier and try again.")

if __name__ == '__main__':
    cli()
