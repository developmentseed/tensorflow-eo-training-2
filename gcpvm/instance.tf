resource "google_compute_firewall" "allow-http" {
  name    = "allow-http-${local.name}"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8888"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http"]
}

data "google_compute_zones" "available" {
}

resource "tls_private_key" "key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}
resource "local_file" "pem" {
  filename        = ".ssh/private_instance_gcp.pem"
  content         = tls_private_key.key.private_key_pem
  file_permission = "400"
}
resource "google_compute_address" "jupyter-static-ip-address" {
  name = "${substr(local.name, 0, 18)}-jupyter-static-ip-address"
}

resource "google_compute_disk" "default" {
  name = "${local.name}-jupyter-disk"
  zone = var.zone #data.google_compute_zones.available.names[0]
  image = "ubuntu-os-cloud/ubuntu-2004-focal-v20220110"
  size  = 300
}
resource "google_compute_instance" "jupyter" {
  count        = 1
  name         = local.name
  machine_type = var.instance-type
  zone         = var.zone // Call it from variable "zone"

  tags = ["http", "http-server"]

  metadata = { ssh-keys = "root:${tls_private_key.key.public_key_openssh}" }

  service_account { scopes = ["storage-full", "cloud-platform"] }

  boot_disk {
    source = google_compute_disk.default.name
  }

  network_interface {
    network = "default"
    access_config {
      nat_ip = google_compute_address.jupyter-static-ip-address.address
    }
  }

  guest_accelerator {
    type  = var.gpu-type  // Type of GPU attached
    count = var.gpu-count // Num of GPU attached
  }

  scheduling {
    on_host_maintenance = "TERMINATE" // Need to terminate GPU on maintenance
  }

  # We connect to our instance via Terraform and remotely executes our script using SSH
  provisioner "remote-exec" {
    script = "minimal-start-up-script.sh"

    connection {
      type        = "ssh"
      host        = google_compute_instance.jupyter[0].network_interface.0.access_config.0.nat_ip
      user        = "root"
      private_key = local_file.pem.content
    }
  }
}

resource "local_file" "vm_id" {
  filename = ".vm-id"
  content  = google_compute_instance.jupyter[0].instance_id
}

resource "local_file" "vm_name" {
  filename = ".vm-name"
  content  = google_compute_instance.jupyter[0].name
}

resource "local_file" "vm_ip" {
  filename = ".vm-ip"
  content  = "root@${google_compute_instance.jupyter[0].network_interface.0.access_config.0.nat_ip}"
}
