variable "UPSTREAM_REGISTRY_HOSTNAME" {
  default = "ghcr.io"
}
variable "UPSTREAM_REGISTRY_PATH" {
  default = "andrewrothstein"
}
variable "UPSTREAM_IMAGE_NAME" {
  default = "docker-ansible"
}
variable "UPSTREAM_IMAGE_TAG" {
  default = "ubuntu_jammy"
}
variable "TARGET_REGISTRY_HOSTNAME" {
  default = "ghcr.io"
}
variable "TARGET_REGISTRY_PATH" {
  default = "andrewrothstein"
}
variable "TARGET_IMAGE_NAME" {
  default = "tasks"
}
variable "TARGET_IMAGE_TAG" {
  default = "ubuntu_jammy"
}

target "both" {
  context = "."
  dockerfile-inline = <<-EOF
  FROM ${UPSTREAM_REGISTRY_HOSTNAME}/${UPSTREAM_REGISTRY_PATH}/${UPSTREAM_IMAGE_NAME}:${UPSTREAM_IMAGE_TAG}
  ADD playbook.yml playbook.yml
  ADD requirements.yml requirements.yml
  RUN ansible-galaxy install \
        -r requirements.yml \
      && \
      ansible-playbook \
        -i localhost, \
        -c local \
        playbook.yml
  EOF
  labels = {
    maintainer = "Andrew Rothstein andrew.rothstein@gmail.com"
  }
  platforms = [
    "linux/amd64",
    "linux/arm64"
  ]
  tags = [
    "${TARGET_REGISTRY_HOSTNAME}/${TARGET_REGISTRY_PATH}/${TARGET_IMAGE_NAME}:${TARGET_IMAGE_TAG}"
  ]
}

target "only" {
  inherits = [
    "both"
  ]
  platforms = [
    "linux/amd64"
  ]
}
