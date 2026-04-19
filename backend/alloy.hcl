discovery.docker "local" {
  host = "unix:///var/run/docker.sock"
}

discovery.relabel "docker_relabel" {
  targets = discovery.docker.local.targets
  rule {
    source_labels = ["__meta_docker_container_name"]
    target_label  = "container"
  }
  rule {
    source_labels = ["__meta_docker_container_label_com_docker_compose_service"]
    target_label  = "service"
  }
}

loki.source.docker "docker_logs" {
  host         = "unix:///var/run/docker.sock"
  targets      = discovery.docker.local.targets
  relabel_rules = discovery.relabel.docker_relabel.rules
  labels = {
    job = "docker-logs",
  }
  forward_to = [loki.write.local.receiver]
}

loki.write "local" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }
}
