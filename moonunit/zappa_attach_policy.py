from itertools import chain

from awacs.aws import Policy, Allow, Statement
from awacs.awslambda import InvokeFunction
from awacs.ec2 import *
from awacs.logs import CreateLogGroup, PutLogEvents, CreateLogStream
from awacs.route53 import Action as Route53Action
from awacs.s3 import PutObject, GetObject, GetBucketNotification, Action as S3Action
from awacs.xray import PutTraceSegments, PutTelemetryRecords

All = "*"
AllResources = ["*"]


def attach_policy_json(**kwargs):
    return attach_policy(**kwargs).to_json()


def attach_policy(*, region, acct_id, bucket_arns):
    return Policy(
        Version='2012-10-17',
        Statement=list(chain.from_iterable([
            stmts_logging(region, acct_id),
            stmts_lambda_invocation(),
            stmts_custom_domain(),
            stmts_vpc(),
            stmts_app(region, acct_id, bucket_arns),
        ]))
    )


def stmts_logging(region, acct_id):
    return [Statement(
        Effect=Allow,
        Action=[CreateLogGroup],
        Resource=[f'arn:aws:logs:{region}:{acct_id}:*']),
        Statement(
            Effect=Allow,
            Action=[CreateLogStream, PutLogEvents],
            Resource=[f'arn:aws:logs:{region}:{acct_id}:*']
            # Resource=[f'arn:aws:logs:{region}:{acct_id}:log-group:/aws/lambda/pvarner-test-1:*'
        ), Statement(
            Effect=Allow,
            Action=[PutTraceSegments, PutTelemetryRecords],
            Resource=AllResources
        )]


def stmts_lambda_invocation():
    return [Statement(
        Effect=Allow,
        Action=[InvokeFunction],
        Resource=AllResources  # TODO: my name
    )]


def stmts_custom_domain():
    return [Statement(
        Effect=Allow,
        Action=[Route53Action(All)],
        Resource=AllResources  # TODO: restrict to my domain?
    )]


def stmts_vpc():
    return [Statement(
        Effect=Allow,
        Action=[
            AttachNetworkInterface,
            CreateNetworkInterface,
            DeleteNetworkInterface,
            DescribeInstances,
            DescribeNetworkInterfaces,
            DetachNetworkInterface,
            ModifyNetworkInterfaceAttribute,
            ResetNetworkInterfaceAttribute
        ],
        Resource=AllResources)]


def stmts_app(region, acct_id, bucket_arns):
    return [
        Statement(
            Effect=Allow,
            Action=[S3Action("*")],
            Resource=[f'{bucket_arn}/*']
        ) for bucket_arn in bucket_arns
    ] + [
        Statement(
            Effect=Allow,
            Action=[S3Action("*")],
            Resource=[f'{bucket_arn}']
        ) for bucket_arn in bucket_arns
    ]
