"""infra for cloud run function for orchestration
Reference doc: https://www.pulumi.com/blog/build-publish-containers-iac/
"""
import os

import cloud_run_images
import cloud_run_offset_tile
import git
import pulumi
import pulumi_gcp as gcp
import titiler_sentinel
from cloud_run_offset_tile import noauth_iam_policy_data
from database import instance, sql_instance_url_with_asyncpg
from utils import construct_name

config = pulumi.Config()

repo = git.Repo(search_parent_directories=True)
git_sha = repo.head.object.hexsha
git_tag = next((tag.name for tag in repo.tags if tag.commit == repo.head.commit), None)

data_raster = config.require("data")

service_name = construct_name("cloud-run-orchestrator")
default = gcp.cloudrun.Service(
    service_name,
    name=service_name,
    location=pulumi.Config("gcp").require("region"),
    template=gcp.cloudrun.ServiceTemplateArgs(
        spec=gcp.cloudrun.ServiceTemplateSpecArgs(
            containers=[
                gcp.cloudrun.ServiceTemplateSpecContainerArgs(
                    image=cloud_run_images.cloud_run_orchestrator_image.name,
                    envs=[
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="DB_URL",
                            value=sql_instance_url_with_asyncpg,
                        ),
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="TITILER_URL",
                            value=titiler_sentinel.lambda_api.api_endpoint.apply(
                                lambda api_endpoint: api_endpoint
                            ),
                        ),
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="INFERENCE_URL",
                            value=cloud_run_offset_tile.default.statuses.apply(
                                lambda statuses: statuses[0].url
                            ),
                        ),
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="AUX_data",
                            value=data_raster,
                        ),
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="GIT_HASH",
                            value=git_sha,
                        ),
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="GIT_TAG",
                            value=git_tag,
                        ),
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="MODEL",
                            value=os.getenv("MODEL"),
                        ),
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="CLOUD_RUN_NAME",
                            value=service_name,
                        ),
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="PROJECT_ID",
                            value=pulumi.Config("gcp").require("project"),
                        ),
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="API_KEY",
                            value=pulumi.Config("project-cloud").require("apikey"),
                        ),
                    ],
                    resources=dict(limits=dict(memory="4Gi", cpu="4000m")),
                ),
            ],
            timeout_seconds=3540,
        ),
        metadata=dict(
            name=service_name + "-" + cloud_run_images.cloud_run_orchestrator_sha,
            annotations={
                "run.googleapis.com/cloudsql-instances": instance.connection_name,
            },
        ),
    ),
    metadata=gcp.cloudrun.ServiceMetadataArgs(
        annotations={
            "run.googleapis.com/launch-stage": "BETA",
        },
    ),
    traffics=[
        gcp.cloudrun.ServiceTrafficArgs(
            percent=100,
            latest_revision=True,
        )
    ],
    opts=pulumi.ResourceOptions(
        depends_on=[
            titiler_sentinel.lambda_api,
            cloud_run_offset_tile.default,
        ]
    ),
)
noauth_iam_policy = gcp.cloudrun.IamPolicy(
    construct_name("cloud-run-noauth-iam-policy-orchestrator"),
    location=default.location,
    project=default.project,
    service=default.name,
    policy_data=noauth_iam_policy_data.policy_data,
)
