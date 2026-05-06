project_name = "taskflow"
env = "dev"
zone = "ru-central1-a"
cidr = "10.10.0.0/24"
platform_id = "standard-v3"
core_fraction = 20
disk_type = "network-hdd"
ssh_public_key = "ssh-ed25519 AAAA..."
allowed_ssh_cidrs = ["YOUR_IP/32"]
ingress_ports = [
  { port = 80,  description = "HTTP",  cidr_blocks = ["0.0.0.0/0"] },
  { port = 443, description = "HTTPS", cidr_blocks = ["0.0.0.0/0"] }
]
user_data = <<-EOF2
#cloud-config
package_update: true
packages:
  - docker.io
runcmd:
  - systemctl enable docker
  - systemctl start docker
EOF2
app_cores = 2
app_memory = 4
app_disk_size = 20
db_cores = 2
db_memory = 4
db_disk_size = 30
redis_cores = 1
redis_memory = 2
redis_disk_size = 10
worker_cores = 2
worker_memory = 4
worker_disk_size = 20
monitoring_cores = 2
monitoring_memory = 4
monitoring_disk_size = 20
edge_cores = 1
edge_memory = 1
edge_disk_size = 10
search_cores = 2
search_memory = 4
search_disk_size = 20