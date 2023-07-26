"""database configurations
"""
import pulumi
import pulumi_gcp as gcp
from utils import construct_name

# See versions at https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/sql_database_instance#database_version
instance = gcp.sql.DatabaseInstance(
    construct_name("database-instance"),
    region=pulumi.Config("gcp").require("region"),
    database_version="POSTGRES_14",
    settings=gcp.sql.DatabaseInstanceSettingsArgs(
        tier=pulumi.Config("db").require("db-instance"),
        backup_configuration=dict(enabled=True),
        database_flags=[dict(name="max_connections", value=200)],
    ),
    deletion_protection=True,
)
db_name = construct_name("database")
database = gcp.sql.Database(db_name, instance=instance.name, name=db_name)
users = gcp.sql.User(
    construct_name("database-users"),
    name=db_name,
    instance=instance.name,
    password=pulumi.Config("db").require_secret("db-password"),
)

sql_instance_url_with_asyncpg = pulumi.Output.concat(
    "postgresql+asyncpg://",
    db_name,
    ":",
    pulumi.Config("db").require_secret("db-password"),
    "@/",
    db_name,
    "?host=/cloudsql/",
    instance.connection_name,
)
sql_instance_url = pulumi.Output.concat(
    "postgresql://",
    db_name,
    ":",
    pulumi.Config("db").require_secret("db-password"),
    "@/",
    db_name,
    "?host=/cloudsql/",
    instance.connection_name,
)
sql_instance_url_alembic = pulumi.Output.concat(
    "postgresql://",
    db_name,
    ":",
    pulumi.Config("db").require_secret("db-password"),
    "@",
    "127.0.0.1",
    "/",
    db_name,
)
