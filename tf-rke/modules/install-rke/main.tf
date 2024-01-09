terraform {
  required_providers {
    rke = {
      source = "rancher/rke"
      version = "~>1"
    }
    local = {
      version = "~>1"
    }
  }
}

resource "rke_cluster" "k8s" {
  kubernetes_version = var.k8s_ver
  dynamic "nodes" {
    for_each = range(1, var.node_count)
    content {
      address = format("core-%03d.nj.drewfus.org", nodes.value)
      user = "arothste"
      role = ["controlplane", "worker", "etcd"]
      ssh_key = file("~/.ssh/id_rsa")
    }
  }
  services {
    kube_api {
      service_cluster_ip_range = var.service_cluster_ip_range
    }
    kube_controller {
      service_cluster_ip_range = var.service_cluster_ip_range
    }
  }
  upgrade_strategy {
    drain = true
    max_unavailable_worker = "20%"
  }
}

resource "local_file" "kube_cluster_yaml" {
  filename = "${path.root}/kube_config_cluster.yml"
  content  = rke_cluster.k8s.kube_config_yaml
}
