import json
from datetime import datetime

import boto3
import cfn_flip
from botocore.exceptions import ClientError
from troposphere import GetAtt, Output, Name, Template, \
    Sub, Export
from troposphere.s3 import Bucket

USER = 'arn:aws:iam::${AWS::AccountId}:user'

All = '*'
AllResources = ['*']


# noinspection PyPep8Naming
def generate_cf_template(*,
                         source_bucket_resource_name, source_bucket_name,
                         assets_bucket_resource_name, assets_bucket_name):
    t = Template(
        Description='A template for creating Bifrost Ingress resources'
    )
    t.version = '2010-09-09'

    define_s3_bucket(
        t=t,
        resource_name=source_bucket_resource_name,
        bucket_name=source_bucket_name
    )
    define_s3_bucket(
        t=t,
        resource_name=assets_bucket_resource_name,
        bucket_name=assets_bucket_name
    )

    return t


def define_s3_bucket(*, t, resource_name, bucket_name):
    s3bucket = t.add_resource(Bucket(resource_name, BucketName=bucket_name))
    t.add_output([
        Output(
            'BucketArn',
            Description=f'ARN of {bucket_name} Bucket',
            Value=GetAtt(resource_name, 'Arn'),
            Export=Export(Name(Sub(f'${{AWS::StackName}}:{resource_name}Arn')))
        )
    ])

    return s3bucket


def stack_exists(client, stack_name):
    stacks = client.list_stacks()['StackSummaries']
    for stack in stacks:
        if stack['StackStatus'] == 'DELETE_COMPLETE':
            continue
        if stack_name == stack['StackName']:
            return True
    return False


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


def create_or_update_aux(*, region, stack_name,
                         source_bucket_resource_name, source_bucket_name,
                         assets_bucket_resource_name, assets_bucket_name):
    template_yaml = cfn_flip.to_yaml(
        generate_cf_template(
            source_bucket_resource_name=source_bucket_resource_name,
            source_bucket_name=source_bucket_name,
            assets_bucket_resource_name=assets_bucket_resource_name,
            assets_bucket_name=assets_bucket_name
        ).to_json()
    )

    client = boto3.client('cloudformation', region_name=region)
    params = {
        'StackName': stack_name,
        'TemplateBody': template_yaml
    }

    try:
        if stack_exists(client, stack_name):
            print(f'Updating stack {stack_name}...', end='', flush=True)
            client.update_stack(**params)
            waiter = client.get_waiter('stack_update_complete')
        else:
            print(f'Requesting "{stack_name}" stack creation... ',
                  end='', flush=True)
            client.create_stack(**params)
            waiter = client.get_waiter('stack_create_complete')
        print(f'waiting for complete... ', end='', flush=True)
        waiter.config.delay = 15
        waiter.config.max_attempts = 20
        waiter.wait(StackName=stack_name)
    except ClientError as ex:
        error_message = ex.response['Error']['Message']
        if error_message == 'No updates are to be performed.':
            print(' no changes.')
        else:
            raise
    else:
        print(' finished.')

    print('Stack output:')
    stack = client.describe_stacks(StackName=stack_name)
    print(json.dumps(stack, indent=2, default=json_serial))
    return stack
