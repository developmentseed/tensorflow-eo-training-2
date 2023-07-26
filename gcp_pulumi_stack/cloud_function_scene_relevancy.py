"""cloud function to select appropriate scenes (over water and IW) from SNS notification"""
import os
import time

import cloud_run_orchestrator
import database
import pulumi
from pulumi_gcp import cloudfunctions, cloudtasks, projects, serviceaccount, storage
from utils import construct_name

stack = pulumi.get_stack()
# We will store the source code to the Cloud Function in a Google Cloud Storage bucket.
bucket = storage.Bucket(
    construct_name("bucket-cloud-function"),
    location="EU",
    labels={"pulumi": "true", "environment": pulumi.get_stack()},
)

# Create the Queue for tasks
queue = cloudtasks.Queue(
    construct_name("queue-cloud-run-orchestrator"),
    location=pulumi.Config("gcp").require("region"),
    rate_limits=cloudtasks.QueueRateLimitsArgs(
        max_concurrent_dispatches=1,
        max_dispatches_per_second=1,
    ),
    retry_config=cloudtasks.QueueRetryConfigArgs(
        max_attempts=3,
        max_backoff="300s",
        max_doublings=1,
        max_retry_duration="4s",
        min_backoff="60s",
    ),
    stackdriver_logging_config=cloudtasks.QueueStackdriverLoggingConfigArgs(
        sampling_ratio=0.9,
    ),
)

function_name = construct_name("cloud-function-scene-relevancy")
config_values = {
    "DB_URL": database.sql_instance_url,
    "GCP_PROJECT": pulumi.Config("gcp").require("project"),
    "GCP_LOCATION": pulumi.Config("gcp").require("region"),
    "QUEUE": queue.name,
    "ORCHESTRATOR_URL": cloud_run_orchestrator.default.statuses[0].url,
    "FUNCTION_NAME": function_name,
    "API_KEY": pulumi.Config("project-cloud").require("apikey"),
    "IS_DRY_RUN": pulumi.Config("project-cloud").require("dryrun_relevancy"),
}

# The Cloud Function source code itself needs to be zipped up into an
# archive, which we create using the pulumi.AssetArchive primitive.
PATH_TO_SOURCE_CODE = "../project_cloud/cloud_function_scene_relevancy"
assets = {}
for file in os.listdir(PATH_TO_SOURCE_CODE):
    location = os.path.join(PATH_TO_SOURCE_CODE, file)
    asset = pulumi.FileAsset(path=location)
    assets[file] = asset

archive = pulumi.AssetArchive(assets=assets)

# Create the single Cloud Storage object, which contains all of the function's
# source code. ("main.py" and "requirements.txt".)
source_archive_object = storage.BucketObject(
    construct_name("source-cloud-function-scene-relevancy"),
    name="handler.py-%f" % time.time(),
    bucket=bucket.name,
    source=archive,
)

# Assign access to cloud SQL
cloud_function_service_account = serviceaccount.Account(
    construct_name("cloud-function"),
    account_id=f"{stack}-cloud-function",
    display_name="Service Account for cloud function.",
)
cloud_function_service_account_iam = projects.IAMMember(
    construct_name("cloud-function-iam"),
    project=pulumi.Config("gcp").require("project"),
    role="projects/project-338116/roles/cloudfunctionscenerelevancyrole",
    member=cloud_function_service_account.email.apply(
        lambda email: f"serviceAccount:{email}"
    ),
)

fxn = cloudfunctions.Function(
    function_name,
    name=function_name,
    entry_point="main",
    environment_variables=config_values,
    region=pulumi.Config("gcp").require("region"),
    runtime="python38",
    source_archive_bucket=bucket.name,
    source_archive_object=source_archive_object.name,
    trigger_http=True,
    service_account_email=cloud_function_service_account.email,
)

invoker = cloudfunctions.FunctionIamMember(
    construct_name("cloud-function-scene-relevancy-invoker"),
    project=fxn.project,
    region=fxn.region,
    cloud_function=fxn.name,
    role="roles/cloudfunctions.invoker",
    member="allUsers",
)
