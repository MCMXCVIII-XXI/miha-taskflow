variable "project_name" { type = string }
variable "env" { type = string }
variable "zone" { type = string }
variable "cidr" { type = string }
variable "platform_id" { type = string }
variable "core_fraction" { type = number }
variable "disk_type" { type = string }
variable "ssh_public_key" { type = string }
variable "allowed_ssh_cidrs" { type = list(string) }
variable "ingress_ports" {
  type = list(object({
    port        = number
    description = string
    cidr_blocks = list(string)
  }))
}
variable "user_data" { type = string }
variable "app_cores" { type = number }
variable "app_memory" { type = number }
variable "app_disk_size" { type = number }
variable "db_cores" { type = number }
variable "db_memory" { type = number }
variable "db_disk_size" { type = number }
variable "redis_cores" { type = number }
variable "redis_memory" { type = number }
variable "redis_disk_size" { type = number }
variable "worker_cores" { type = number }
variable "worker_memory" { type = number }
variable "worker_disk_size" { type = number }
variable "monitoring_cores" { type = number }
variable "monitoring_memory" { type = number }
variable "monitoring_disk_size" { type = number }
variable "edge_cores" { type = number }
variable "edge_memory" { type = number }
variable "edge_disk_size" { type = number }
variable "search_cores" { type = number }
variable "search_memory" { type = number }
variable "search_disk_size" { type = number } 
variable "yc_token" {
  type = string
  sensitive = true
}
variable "cloud_id" { type = string }
variable "folder_id" { type = string }