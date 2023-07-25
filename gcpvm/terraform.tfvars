instance-type = "n1-standard-8" # "n1-standard-8" is a good default. only n1 types can add gpus https://stackoverflow.com/questions/53968149/add-gpu-to-an-existing-vm-instance-google-compute-engine
# change to n1-standard-32 for a dataset creation vm
gpu-count = 1
gpu-type  = "nvidia-tesla-t4" # https://cloud.google.com/compute/docs/gpus/gpu-regions-zones alternative GPU options for europe-west4
location  = "us-west4"        # don't change this unless you know you need to. only west4 has a wide range of GPU types
zone      = "us-west4-b"
