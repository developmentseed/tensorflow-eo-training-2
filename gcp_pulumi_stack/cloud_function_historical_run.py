"""cloud function to select appropriate scenes (over water and IW) from SNS notification"""
import os
import time

import cloud_function_scene_relevancy
import cloud_run_orchestrator
import database
import pulumi
from pulumi_gcp import cloudfunctions, storage
from utils import construct_name

stack = pulumi.get_stack()

function_name = construct_name("cloud-function-historical-run")
config_values = {
    "DB_URL": database.sql_instance_url,
    "GCP_PROJECT": pulumi.Config("gcp").require("project"),
    "GCP_LOCATION": pulumi.Config("gcp").require("region"),
    "QUEUE": cloud_function_scene_relevancy.queue.name,
    "ORCHESTRATOR_URL": cloud_run_orchestrator.default.statuses[0].url,
    "FUNCTION_NAME": function_name,
    "SCIHUB_USERNAME": pulumi.Config("scihub").require("username"),
    "SCIHUB_PASSWORD": pulumi.Config("scihub").require("password"),
    "API_KEY": pulumi.Config("project-cloud").require("apikey"),
    "IS_DRY_RUN": pulumi.Config("project-cloud").require("dryrun_historical"),
}

# The Cloud Function source code itself needs to be zipped up into an
# archive, which we create using the pulumi.AssetArchive primitive.
PATH_TO_SOURCE_CODE = "../project_cloud/cloud_function_historical_run"
assets = {}
for file in os.listdir(PATH_TO_SOURCE_CODE):
    location = os.path.join(PATH_TO_SOURCE_CODE, file)
    asset = pulumi.FileAsset(path=location)
    assets[file] = asset

archive = pulumi.AssetArchive(assets=assets)

# Create the single Cloud Storage object, which contains all of the function's
# source code. ("main.py" and "requirements.txt".)
source_archive_object = storage.BucketObject(
    construct_name("source-cloud-function-historical-run"),
    name="handler.py-%f" % time.time(),
    bucket=cloud_function_scene_relevancy.bucket.name,
    source=archive,
)

fxn = cloudfunctions.Function(
    function_name,
    name=function_name,
    entry_point="main",
    environment_variables=config_values,
    region=pulumi.Config("gcp").require("region"),
    runtime="python38",
    source_archive_bucket=cloud_function_scene_relevancy.bucket.name,
    source_archive_object=source_archive_object.name,
    trigger_http=True,
    service_account_email=cloud_function_scene_relevancy.cloud_function_service_account.email,
    timeout=500,
)

invoker = cloudfunctions.FunctionIamMember(
    construct_name("cloud-function-historical-run-invoker"),
    project=fxn.project,
    region=fxn.region,
    cloud_function=fxn.name,
    role="roles/cloudfunctions.invoker",
    member="allUsers",
)
