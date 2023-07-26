"""infra for cloud run function for orchestration
Reference doc: https://www.pulumi.com/blog/build-publish-containers-iac/
"""
import cloud_run_images
import pulumi
import pulumi_gcp as gcp
from cloud_run_offset_tile import noauth_iam_policy_data
from database import instance, sql_instance_url
from utils import construct_name

config = pulumi.Config()

service_name = construct_name("cloud-run-tifeatures")
default = gcp.cloudrun.Service(
    service_name,
    name=service_name,
    location=pulumi.Config("gcp").require("region"),
    template=gcp.cloudrun.ServiceTemplateArgs(
        spec=gcp.cloudrun.ServiceTemplateSpecArgs(
            containers=[
                gcp.cloudrun.ServiceTemplateSpecContainerArgs(
                    image=cloud_run_images.cloud_run_tifeatures_image.name,
                    envs=[
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="DATABASE_URL",
                            value=sql_instance_url,
                        ),
                        gcp.cloudrun.ServiceTemplateSpecContainerEnvArgs(
                            name="TIFEATURES_NAME", value="project OGC API"
                        ),
                    ],
                    resources=dict(limits=dict(memory="2Gi", cpu="4000m")),
                ),
            ],
            timeout_seconds=420,
        ),
        metadata=dict(
            name=service_name + "-" + cloud_run_images.cloud_run_tifeatures_sha,
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
)
noauth_iam_policy = gcp.cloudrun.IamPolicy(
    construct_name("cloud-run-noauth-iam-policy-tifeatures"),
    location=default.location,
    project=default.project,
    service=default.name,
    policy_data=noauth_iam_policy_data.policy_data,
)
