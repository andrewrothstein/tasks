import json

import dagger
from dagger import dag, function, object_type


@object_type
class DaggerCi:
    @function
    async def build_image(
        self,
        source: dagger.Directory,
        upstream_registry: str = "ghcr.io",
        upstream_registry_path: str = "andrewrothstein",
        upstream_image_name: str = "docker-ansible",
        target_registry: str = "ghcr.io",
        target_registry_path: str = "andrewrothstein",
        target_image_name: str = "tasks",
        platform: str = "linux/amd64",
        os: str = "ubuntu",
        os_ver: str = "jammy",
    ) -> dagger.Container:
        """Build a container image for the given OS and platform."""
        upstream_tag = f"0.0.0-{os}.{os_ver}"
        upstream_image = (
            f"{upstream_registry}/{upstream_registry_path}"
            f"/{upstream_image_name}:{upstream_tag}"
        )

        task_binary = (
            dag.container()
            .from_("alpine:latest")
            .with_exec(["apk", "--no-cache", "add", "ca-certificates", "curl"])
            .with_exec([
                "sh", "-c",
                "curl --location https://taskfile.dev/install.sh | sh -s"
                " -- -d -b /tmp",
            ])
            .file("/tmp/task")
        )

        return (
            dag.container(platform=dagger.Platform(platform))
            .from_(upstream_image)
            .with_env_variable(
                "PATH",
                "/root/.local/bin:"
                "/usr/local/sbin:/usr/local/bin:"
                "/usr/sbin:/usr/bin:/sbin:/bin",
            )
            .with_file("/tmp/task", task_binary)
            .with_directory("/tasks", source)
            .with_workdir("/tasks")
            .with_exec(["/tmp/task", "-t", "ansible-local.yml"])
            .with_exec(["rm", "/tmp/task"])
            .with_label(
                "maintainer",
                "Andrew Rothstein andrew.rothstein@gmail.com",
            )
        )

    @function
    async def build_and_push(
        self,
        source: dagger.Directory,
        github_token: dagger.Secret,
        github_actor: str = "andrewrothstein",
        target_registry: str = "ghcr.io",
        target_registry_path: str = "andrewrothstein",
        target_image_name: str = "tasks",
        platform: str = "linux/amd64",
        os: str = "ubuntu",
        os_ver: str = "jammy",
    ) -> str:
        """Build and push a single platform image."""
        target_tag = f"0.0.0-{os}.{os_ver}"
        target_image = (
            f"{target_registry}/{target_registry_path}"
            f"/{target_image_name}:{target_tag}"
        )

        container = await self.build_image(
            source=source,
            platform=platform,
            os=os,
            os_ver=os_ver,
        )

        container = container.with_registry_auth(
            target_registry,
            github_actor,
            github_token,
        )

        published = await container.publish(target_image)
        return f"Published: {published}"

    @function
    async def build_matrix_entry(
        self,
        source: dagger.Directory,
        github_token: dagger.Secret,
        os: str,
        os_ver: str,
        platforms: str = "linux/amd64",
        github_actor: str = "andrewrothstein",
    ) -> list[str]:
        """Build and push images for a single matrix entry."""
        architectures = [p.strip() for p in platforms.split(",")]

        errors = []
        results = []
        for arch in architectures:
            try:
                result = await self.build_and_push(
                    source=source,
                    github_token=github_token,
                    github_actor=github_actor,
                    platform=arch,
                    os=os,
                    os_ver=os_ver,
                )
                results.append(f"{arch}: {result}")
            except Exception as e:
                errors.append(f"{arch}: {e}")
        if errors:
            raise RuntimeError(
                f"Build failed for {os}.{os_ver}: " + "; ".join(errors)
            )
        return results

    @function
    async def validate_matrix_entry(
        self,
        source: dagger.Directory,
        os: str,
        os_ver: str,
        platforms: str = "linux/amd64",
    ) -> list[str]:
        """Build images for a single matrix entry without pushing (PR validation)."""
        architectures = [p.strip() for p in platforms.split(",")]

        errors = []
        results = []
        for arch in architectures:
            try:
                container = await self.build_image(
                    source=source,
                    platform=arch,
                    os=os,
                    os_ver=os_ver,
                )
                await container.sync()
                results.append(f"{arch}: Build successful for {os}.{os_ver}")
            except Exception as e:
                errors.append(f"{arch}: {e}")
        if errors:
            raise RuntimeError(
                f"Validation failed for {os}.{os_ver}: " + "; ".join(errors)
            )
        return results

    @function
    async def build_all(
        self,
        source: dagger.Directory,
        github_token: dagger.Secret,
        github_actor: str = "andrewrothstein",
        matrix_file: str = "platform-matrix-v1.json",
    ) -> list[str]:
        """Build and push all platform images from the matrix."""
        matrix_content = await source.file(matrix_file).contents()
        entries = json.loads(matrix_content)

        results = []
        for entry in entries:
            entry_results = await self.build_matrix_entry(
                source=source,
                github_token=github_token,
                github_actor=github_actor,
                os=entry["OS"],
                os_ver=entry["OS_VER"],
                platforms=entry.get("PLATFORMS", "linux/amd64"),
            )
            results.extend(entry_results)
        return results
