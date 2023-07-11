variable "location" {
  type        = string
  description = "Location of the resources"
  default     = "europe-west4"
  # Check available zones for instance type in https://cloud.google.com/compute/docs/regions-zones
  # For N1 machines, with GPU:
  ## Europe
  # europe-west1 - 	St. Ghislain, Belgium, Europe
  # europe-west2 - London, England, Europe
  # europe-west3 - Frankfurt, Germany Europe
  # europe-west4 - Eemshaven, Netherlands, Europe # has most gpu types
  # europe-west6 - 	Zurich, Switzerland, Europe
  ## North America
  # northamerica-northeast1 - Montréal, Québec, North America
  # us-central1 - Council Bluffs, Iowa, North America
  # us-east1 - Moncks Corner, South Carolina, North America
  # us-east4 - Ashburn, Virginia, North America
  # us-west1 - The Dalles, Oregon, North America
  # us-west2 - 	Los Angeles, California, North America
  # us-west4 - Las Vegas, Nevada, North America 
}

variable "zone" {
  type        = string
  description = "Location of the resources"
  default     = "europe-west4-a"
}

variable "instance-type" {
  # list of machine types, select the lowest cost one that gets the job done
  # https://gcpinstances.doit-intl.com/
  type        = string
  description = "Instance type to deploy"
  default     = "n1-standard-4"
}

variable "project" {
  type        = string
  description = "Project"
  default     = "your-gcp-project-id"
}

variable "gpu-count" {
  type        = number
  description = "how many gpus to attach to instance"
  default     = 1
}

variable "gpu-type" {
  type        = string
  description = "type of gpu(s) to attach to instance"
  default     = "nvidia-tesla-t4"
  # t4 is cheapest: https://cloud.google.com/compute/docs/gpus#performance_comparison_chart
  # see here for other options https://cloud.google.com/compute/docs/gpus#nvidia_gpus_for_compute_workloads
  # and make sure you are in the correct region, most regions don't have all types of gpus
  # https://cloud.google.com/compute/docs/gpus/gpu-regions-zones
}
