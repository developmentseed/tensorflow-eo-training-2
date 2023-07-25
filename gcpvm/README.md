# Deploy GPU ML instance in GCP

## Setup

Follow the steps described in [this](https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/provider_reference#authentication) to setup GCP authentication.

Install the [terraform CLI](https://learn.hashicorp.com/tutorials/terraform/install-cli).

## Adapt `terraform.tfvars` file
Navigate to the folder containing `main.tf`. Adapt the `terraform.tfvars` file as needed. Currently we are using europe-west-4 since the Sentinel-1 data source is in Frankfurt and europe-west-4 has a variety of gpus.

## Deploy

Navigate to the folder containing the `main.tf` file. Run `terraform init`.

Check your deployment with `terraform plan`.

If you get a credentials error, you might need to run `gcloud auth application-default login`.

You can create your instance with `terraform apply`. Hit `y` if you want to create the VM.

This will create a GCP Compute instance, and save in your local machine a private ssh key (in `.ssh/`), and a series of `.vm-X` files containing identity information for your instance. **Do not delete or modify this files!**

## The VM

This VM contains a conda environment `fastai2` that can be activated with `conda activate fastai2` and edited by editing `minimal-start-up-script.sh`, which runs commands when `terraform apply` is called. See the `start-up-script.sh` for reference (this was used to create the custom cerulean base image) and in particular use `-y` flags when installing packages with `conda` so that there is no waiting for manual response.

The VM also comes with docker and jupyter with port forwarding to your local machine (you can copy and paste a jupyter link on the VM to your local machine's browser).

## `make` tools

You can now use the set of tools included in the `Makefile`. Adapt this file if needed in case you want to change the remote and local path to copy files into the instance.

- `make ssh`: connects to your instance in your shell. This also maps the port 8888 in the instance to your localhost, allowing you to serve a jupyter instance via this ssh tunnel (for instance by running `jupyter lab --allow-root`).
- `make start`, `make stop`, `make status` : Start, stop and check the status of your instance. **Important: if you are not using your instance, make sure to run `make stop` to avoid excessive costs! Don't worry, your instance state and files are safe.**
- `make syncup` and `make syncdown`: Copies files in your folder from and to your instance.

## Destroy

When you finish all work associated with this instance make sure to run `terraform destroy`. This will delete the ssh key in `.ssh` and all `.vm-X` files.

**Important: when you destroy your instance, all files and instance state are deleted with it so make sure to back them up to GCS or locally if needed!**

## The Workflow
In short, do the following to deploy the VM, sync the git directory, and ssh with port forwarding

```
cd gcpvm
terraform init
terraform apply
make syncup
make ssh
```

If you need to, edit the `minimal-start-up-script.sh` to change what is installe donto the terraform VM during `terraform apply`. the use of this script is defined in `instance.tf`. This script does not support setting up permanent and persistent mounting, hence the bash aliases for bucket mounting `cdata` and `cdata2`. It also doesn't support activating python environments to install things into them, so we need to do that after make syncup and make ssh manually.


## Notes on the Instance

The instance will have access to all buckets in the project. These buckets will be mounted under the directories `/root/data`. And `/root/data-cv2` after calling `cdata` and `cdata2`. They can only be accessed by specifying paths to the contents of their subdirs. See the [gcsfuse mounting instructions](https://github.com/GoogleCloudPlatform/gcsfuse/blob/master/docs/mounting.md) for more details.



