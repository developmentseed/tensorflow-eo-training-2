terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "3.1.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "2.1.0"
    }
  }

  required_version = ">= 0.14.9"
}
provider "google" {
  region  = var.location
  project = var.project
}


locals {
  name = "ml-jupyter-${uuid()}"
}
