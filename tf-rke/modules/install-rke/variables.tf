variable "k8s_ver" {
  default = "v1.25.9-rancher2-1"
}

variable "node_count" {
  default = 1
}

variable "service_cluster_ip_range" {
  default = "10.43.0.0/16"
}

variable "cluster_cidr" {
  default = "10.42.0.0/16"
}

variable "cluster_dns_server" {
  default = "10.43.0.10"
}

variable "cluster_domain" {
  default = "k8s.nj.drewfus.org"
}
