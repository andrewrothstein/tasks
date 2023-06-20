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
  FROM alpine:latest as downloader
  RUN apk --no-cache add ca-certificates curl
  RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /tmp
  RUN chmod +x /tmp/task

  FROM ${UPSTREAM_REGISTRY_HOSTNAME}/${UPSTREAM_REGISTRY_PATH}/${UPSTREAM_IMAGE_NAME}:${UPSTREAM_IMAGE_TAG}
  COPY --from=downloader /tmp/task /tmp/task
  ADD . /tasks
  WORKDIR /tasks
  RUN /tmp/task -t ansible-local.yml; rm /tmp/task
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
