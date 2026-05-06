terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

module "vm" {
  source             = "../vm"
  name               = var.vm_name
  hostname           = var.vm_hostname
  platform_id        = var.platform_id
  zone               = var.zone
  cores              = var.cores
  memory             = var.memory
  core_fraction      = var.core_fraction
  image_id           = var.image_id
  disk_size          = var.disk_size
  disk_type          = var.disk_type
  subnet_id          = var.subnet_id
  nat                = var.nat
  security_group_ids = var.security_group_ids
  ssh_public_key     = var.ssh_public_key
  user_data          = var.user_data
}