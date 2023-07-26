# Deploy GPU ML instance in GCP

## Setup

Follow the steps described in [this](https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/provider_reference#authentication) to setup GCP authentication.

Install the [terraform CLI](https://learn.hashicorp.com/tutorials/terraform/install-cli).

## Adapt `terraform.tfvars` file
Navigate to the folder containing `main.tf`. Adapt the `terraform.tfvars` file as needed.

## Deploy

Navigate to the folder containing the `main.tf` file. Run `terraform init`.

Check your deployment with `terraform plan`.

If you get a credentials error, you might need to run `gcloud auth application-default login`.

You can create your instance with `terraform apply`. Hit `y` if you want to create the VM.

This will create a GCP Compute instance, and save in your local machine a private ssh key (in `.ssh/`), and a series of `.vm-X` files containing identity information for your instance. **Do not delete or modify this files!**

## Manual VM setup steps

`make ssh` into the instance.

To set up git:
```
git config --global user.name "Ryan Avery"
git config --global user.email "ryan@developmentseed.org"
```

to edit your global config file.

Then,

```
type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
&& sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
&& sudo apt update \
&& sudo apt install gh -y
```

and

```
sudo apt update
sudo apt install gh
```

to install the Github CLI. Don't install it with snap, because the ssh key will be created in the wrong directory in the next step.

Then, `gh auth login`. Select the ssh option to add a new ssh key for the vm so you can push and access private repos. Also select login with web browser even though the vm doesn't have a browser and follow the instructions. This is to ensure that the github auth is set up correctly. You'll then need to use the gh cli to manage repos and checking out PRs. Or you can look up and set up ssh auth with git instead. 

Then, `gh repo clone gh-account/gh-repo` to clone your repo.

```bash
ubuntu@ip-172-31-27-67:~$ gh auth login
? What account do you want to log into? GitHub.com
? What is your preferred protocol for Git operations? SSH
? Generate a new SSH key to add to your GitHub account? Yes
? Enter a passphrase for your new SSH key (Optional)
? Title for your SSH key: GitHub CLI
? How would you like to authenticate GitHub CLI? Login with a web browser
ubuntu@ip-172-31-27-67:~$ gh repo clone developmentseed/project
Cloning into 'project'...
The authenticity of host 'github.com (140.82.121.3)' can't be established.
ECDSA key fingerprint is SHA256:p2QAMXNIC1TJYWeIOttrVc98/R1BUFWu3/LiyKgUfQM.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
```

### Docker setup
Docker is the easiest way to spin up environments for GPU-dependent programs, since these are complicated to install. 

Follow all instructions here, first installing docker, then following the instructions for nvidia-container-toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html Including the instructions on installing docker with the convenience script. Then follow the post install instructions: https://docs.docker.com/engine/install/linux-postinstall/

They're included here for convenience, but refer back to the link in case these don't work in case they got updated by NVIDIA or Docker.

```
$ curl https://get.docker.com | sh \
  && sudo systemctl --now enable docker
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit-base
sudo usermod -aG docker $USER
```
log out and log back in with `make ssh`

```
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)       && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg       && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list |             sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' |             sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://nvidia.github.io/libnvidia-container/stable/ubuntu18.04/$(ARCH) /
#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://nvidia.github.io/libnvidia-container/experimental/ubuntu18.04/$(ARCH) /
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

If a window comes up listing services to restart when running `apt` commands, you can run `sudo reboot` and ssh back in and the window will be gone.

### Connect to the VM with VSCode

For VSCode setup, go to Remote Explorer, select Remotes, select the wheel icon and edit the ssh config file. Add this block, adapting your absolute path to your pem key in the .ssh folder in gcpvm.

 Note for Windows Subsystem for Linux users: I had to manually copy the .pem to another folder on the Windows partition so that VSCode could detect the .pem key. If on Mac point to the project .ssh pem key created by terraform at `gcpvm/.ssh/private_instance_gcp.pem`.

```
Host project-Dev
    HostName content from .vm-ip
    IdentityFile "~/project/.ssh/private_instance_gcp.pem"
    LocalForward 8888 localhost:8888
    LocalForward 6006 localhost:6006
    IdentitiesOnly yes
```

## `make` tools

You can now use the set of tools included in the `Makefile`. Adapt this file if needed in case you want to change the remote and local path to copy files into the instance.

- `make ssh`: connects to your instance in your shell. This also maps the port 8888 in the instance to your localhost, allowing you to serve a jupyter instance via this ssh tunnel (for instance by running `jupyter lab --allow-root`).
- `make start`, `make stop`, `make status` : Start, stop and check the status of your instance. **Important: if you are not using your instance, make sure to run `make stop` to avoid excessive costs! Don't worry, your instance state and files are safe.**
- `make syncup` and `make syncdown`: Copies files in your folder from and to your instance.

## Destroy

When you finish all work associated with this instance make sure to run `terraform destroy`. This will delete the ssh key in `.ssh` and all `.vm-X` files.

**Important: when you destroy your instance, all files and instance state are deleted with it so make sure to back them up to GCS or locally if needed!**


## Notes on the Instance

The instance will have access to all buckets in the project, but not via the filesystem. Use python libraries that support accessing cloud urls, like `pandas`, `xarray`, and `rasterio`. And cloud-native formats that support partial and parallel reads from cloud storage, namely, cloud optimized geotiffs.


