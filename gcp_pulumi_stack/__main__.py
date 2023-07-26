"""A Python Pulumi program"""

import cloud_function_historical_run
import cloud_function_scene_relevancy
import cloud_run_offset_tile
import cloud_run_orchestrator
import cloud_run_tifeatures
import database
import pulumi
import sns_subscription
import titiler_sentinel as titiler_sentinel

# Export the DNS name of the bucket
pulumi.export("titiler_sentinel_url", titiler_sentinel.lambda_api.api_endpoint)
pulumi.export(
    "cloud_run_offset_tile_url", cloud_run_offset_tile.default.statuses[0].url
)
pulumi.export(
    "cloud_run_orchestrator_url", cloud_run_orchestrator.default.statuses[0].url
)
pulumi.export("cloud_run_tifeatures_url", cloud_run_tifeatures.default.statuses[0].url)
pulumi.export("database_url", database.sql_instance_url)
pulumi.export("database_instance_name", database.instance.connection_name)
pulumi.export("database_url_alembic", database.sql_instance_url_alembic)
pulumi.export(
    "scene_relevancy_url", cloud_function_scene_relevancy.fxn.https_trigger_url
)
pulumi.export("historical_run_url", cloud_function_historical_run.fxn.https_trigger_url)
pulumi.export("sns_topic_subscription", sns_subscription.sentinel1_sqs_target.arn)
pulumi.export("api_key", pulumi.Config("project-cloud").require("apikey"))
