terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

resource "yandex_vpc_security_group" "this" {
  name       = var.name
  network_id = var.network_id

  ingress {
    protocol       = "TCP"
    description    = "SSH"
    v4_cidr_blocks = var.allowed_ssh_cidrs
    port           = 22
  }

  dynamic "ingress" {
    for_each = var.ingress_ports
    content {
      protocol       = "TCP"
      description    = ingress.value.description
      v4_cidr_blocks = ingress.value.cidr_blocks
      port           = ingress.value.port
    }
  }

  egress {
    protocol       = "ANY"
    description    = "Allow all outbound"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}
