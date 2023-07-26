"""titiler sentinel infra module"""
import pulumi
import pulumi_aws as aws
from utils import construct_name, create_package, filebase64sha256

s3_bucket = aws.s3.Bucket(construct_name("titiler-lambda-archive"))

lambda_package_path = create_package("../")
lambda_package_archive = pulumi.FileArchive(lambda_package_path)

lambda_obj = aws.s3.BucketObject(
    construct_name("titiler-lambda-archive"),
    key="package.zip",
    bucket=s3_bucket.id,
    source=lambda_package_archive,
)

# Role policy to fetch S3
iam_for_lambda = aws.iam.Role(
    construct_name("lambda-titiler-role"),
    assume_role_policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
""",
)

# Lambda function
lambda_titiler_sentinel = aws.lambda_.Function(
    resource_name=construct_name("lambda-titiler-sentinel"),
    s3_bucket=s3_bucket.id,
    s3_key=lambda_obj.key,
    source_code_hash=filebase64sha256(lambda_package_path),
    runtime="python3.8",
    role=iam_for_lambda.arn,
    memory_size=3008,
    timeout=10,
    handler="handler.handler",
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif,.TIF,.tiff",
            "GDAL_CACHEMAX": "200",
            "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
            "GDAL_INGESTED_BYTES_AT_OPEN": "32768",
            "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
            "GDAL_HTTP_MULTIPLEX": "YES",
            "GDAL_HTTP_VERSION": "2",
            "PYTHONWARNINGS": "ignore",
            "VSI_CACHE": "TRUE",
            "VSI_CACHE_SIZE": "5000000",
            "AWS_REQUEST_PAYER": "requester",
            "RIO_TILER_MAX_THREADS": 1,
            "API_KEY": pulumi.Config("project-cloud").require("apikey"),
        },
    ),
    opts=pulumi.ResourceOptions(depends_on=[lambda_obj]),
)

lambda_s3_policy = aws.iam.Policy(
    construct_name("lambda-titiler-policy"),
    description="IAM policy for Lambda to interact with S3",
    policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::sentinel-s1-l1c/*",
      "Effect": "Allow"
    }
  ]}""",
)
aws.iam.RolePolicyAttachment(
    construct_name("lambda-titiler-attachment"),
    policy_arn=lambda_s3_policy.arn,
    role=iam_for_lambda.name,
)
aws.iam.RolePolicyAttachment(
    construct_name("lambda-titiler-attachment2"),
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    role=iam_for_lambda.name,
)

# API gateway
lambda_permission = aws.lambda_.Permission(
    construct_name("lambda-titiler-permission"),
    action="lambda:InvokeFunction",
    principal="apigateway.amazonaws.com",
    function=lambda_titiler_sentinel,
)
lambda_api = aws.apigatewayv2.Api(
    construct_name("lambda-titiler-api"), protocol_type="HTTP"
)
lambda_integration = aws.apigatewayv2.Integration(
    construct_name("lambda-titiler-integration"),
    api_id=lambda_api.id,
    integration_type="AWS_PROXY",
    integration_uri=lambda_titiler_sentinel.invoke_arn,
)
lambda_route = aws.apigatewayv2.Route(
    construct_name("lambda-titiler-route"),
    api_id=lambda_api.id,
    route_key="ANY /{proxy+}",
    target=pulumi.Output.concat("integrations/", lambda_integration.id),
)
lambda_stage = aws.apigatewayv2.Stage(
    construct_name("lambda-titiler-stage"),
    api_id=lambda_api.id,
    name="$default",
    auto_deploy=True,
    opts=pulumi.ResourceOptions(depends_on=[lambda_route]),
)
