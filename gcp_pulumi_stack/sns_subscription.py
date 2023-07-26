"""Subscription to SNS topic"""
import cloud_function_scene_relevancy
import pulumi
import pulumi_aws as aws
from utils import construct_name

iam_for_lambda = aws.iam.Role(
    construct_name("lambda-sentinel1-iam"),
    assume_role_policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
""",
)

lambda_sentinel1_topic = aws.lambda_.Function(
    resource_name=construct_name("lambda-sentinel1-subscription"),
    runtime="python3.8",
    code=pulumi.AssetArchive(
        {
            ".": pulumi.FileArchive("../project_cloud/lambda_sentinel1_subscription"),
        }
    ),
    handler="handler.lambda_handler",
    role=iam_for_lambda.arn,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "FUNCTION_URL": cloud_function_scene_relevancy.fxn.https_trigger_url
        },
    ),
    layers=["arn:aws:lambda:eu-central-1:xxxxxxxxx:layer:Klayers-p38-requests:4"],
)
# Give SNS permissions to invoke the Lambda
lambda_permission = aws.lambda_.Permission(
    construct_name("lambda-sentinel1-permission"),
    action="lambda:InvokeFunction",
    principal="sns.amazonaws.com",
    function=lambda_sentinel1_topic,
)

sentinel1_sqs_target = aws.sns.TopicSubscription(
    construct_name("sentinel1-subscription"),
    protocol="lambda",
    endpoint=lambda_sentinel1_topic.arn,
    confirmation_timeout_in_minutes=5,
    topic="arn:aws:sns:eu-central-1:xxxxxxxx:SentinelS1L1C",
)
