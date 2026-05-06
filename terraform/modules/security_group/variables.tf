variable "name" {
  type = string
}

variable "network_id" {
  type = string
}

variable "allowed_ssh_cidrs" {
  type = list(string)
}

variable "ingress_ports" {
  type = list(object({
    port        = number
    description = string
    cidr_blocks = list(string)
  }))
  default = []
}
