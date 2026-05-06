terraform {
  required_version = ">= 1.5.0"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.201.0"
    }
  }
}

provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.cloud_id
  folder_id = var.folder_id
  zone      = var.zone
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

module "network" {
  source      = "../../modules/network"
  name        = "${var.project_name}-${var.env}-network"
  subnet_name = "${var.project_name}-${var.env}-public-subnet"
  zone        = var.zone
  cidr        = var.cidr
}

module "security_group" {
  source            = "../../modules/security_group"
  name              = "${var.project_name}-${var.env}-sg"
  network_id        = module.network.network_id
  allowed_ssh_cidrs = var.allowed_ssh_cidrs
  ingress_ports     = var.ingress_ports
}
module "app" {
  source             = "../../modules/app"
  vm_name            = "${var.project_name}-${var.env}-app"
  vm_hostname        = "${var.project_name}-${var.env}-app"
  platform_id        = var.platform_id
  zone               = var.zone
  cores              = var.app_cores
  memory             = var.app_memory
  core_fraction      = var.core_fraction
  image_id           = data.yandex_compute_image.ubuntu.id
  disk_size          = var.app_disk_size
  disk_type          = var.disk_type
  subnet_id          = module.network.subnet_id
  nat                = true
  security_group_ids = [module.security_group.security_group_id]
  ssh_public_key     = var.ssh_public_key
  user_data          = var.user_data
}

module "db" {
  source             = "../../modules/db"
  vm_name            = "${var.project_name}-${var.env}-db"
  vm_hostname        = "${var.project_name}-${var.env}-db"
  platform_id        = var.platform_id
  zone               = var.zone
  cores              = var.db_cores
  memory             = var.db_memory
  core_fraction      = var.core_fraction
  image_id           = data.yandex_compute_image.ubuntu.id
  disk_size          = var.db_disk_size
  disk_type          = var.disk_type
  subnet_id          = module.network.subnet_id
  nat                = false
  security_group_ids = [module.security_group.security_group_id]
  ssh_public_key     = var.ssh_public_key
  user_data          = var.user_data
}

module "redis" {
  source             = "../../modules/redis"
  vm_name            = "${var.project_name}-${var.env}-redis"
  vm_hostname        = "${var.project_name}-${var.env}-redis"
  platform_id        = var.platform_id
  zone               = var.zone
  cores              = var.redis_cores
  memory             = var.redis_memory
  core_fraction      = var.core_fraction
  image_id           = data.yandex_compute_image.ubuntu.id
  disk_size          = var.redis_disk_size
  disk_type          = var.disk_type
  subnet_id          = module.network.subnet_id
  nat                = false
  security_group_ids = [module.security_group.security_group_id]
  ssh_public_key     = var.ssh_public_key
  user_data          = var.user_data
}

module "workers" {
  source             = "../../modules/workers"
  vm_name            = "${var.project_name}-${var.env}-workers"
  vm_hostname        = "${var.project_name}-${var.env}-workers"
  platform_id        = var.platform_id
  zone               = var.zone
  cores              = var.worker_cores
  memory             = var.worker_memory
  core_fraction      = var.core_fraction
  image_id           = data.yandex_compute_image.ubuntu.id
  disk_size          = var.worker_disk_size
  disk_type          = var.disk_type
  subnet_id          = module.network.subnet_id
  nat                = false
  security_group_ids = [module.security_group.security_group_id]
  ssh_public_key     = var.ssh_public_key
  user_data          = var.user_data
}

module "monitoring" {
  source             = "../../modules/monitoring"
  vm_name            = "${var.project_name}-${var.env}-monitoring"
  vm_hostname        = "${var.project_name}-${var.env}-monitoring"
  platform_id        = var.platform_id
  zone               = var.zone
  cores              = var.monitoring_cores
  memory             = var.monitoring_memory
  core_fraction      = var.core_fraction
  image_id           = data.yandex_compute_image.ubuntu.id
  disk_size          = var.monitoring_disk_size
  disk_type          = var.disk_type
  subnet_id          = module.network.subnet_id
  nat                = false
  security_group_ids = [module.security_group.security_group_id]
  ssh_public_key     = var.ssh_public_key
  user_data          = var.user_data
}

module "search" {
  source             = "../../modules/search"
  vm_name            = "${var.project_name}-${var.env}-search"
  vm_hostname        = "${var.project_name}-${var.env}-search"
  platform_id        = var.platform_id
  zone               = var.zone
  cores              = var.search_cores
  memory             = var.search_memory
  core_fraction      = var.core_fraction
  image_id           = data.yandex_compute_image.ubuntu.id
  disk_size          = var.search_disk_size
  disk_type          = var.disk_type
  subnet_id          = module.network.subnet_id
  nat                = false
  security_group_ids = [module.security_group.security_group_id]
  ssh_public_key     = var.ssh_public_key
  user_data          = var.user_data
}

module "edge" {
  source             = "../../modules/edge"
  vm_name            = "${var.project_name}-${var.env}-edge"
  vm_hostname        = "${var.project_name}-${var.env}-edge"
  platform_id        = var.platform_id
  zone               = var.zone
  cores              = var.edge_cores
  memory             = var.edge_memory
  core_fraction      = var.core_fraction
  image_id           = data.yandex_compute_image.ubuntu.id
  disk_size          = var.edge_disk_size
  disk_type          = var.disk_type
  subnet_id          = module.network.subnet_id
  nat                = true
  security_group_ids = [module.security_group.security_group_id]
  ssh_public_key     = var.ssh_public_key
  user_data          = var.user_data
}
