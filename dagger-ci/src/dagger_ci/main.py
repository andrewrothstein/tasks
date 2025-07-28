import dagger
from dagger import dag, function, object_type
import json
from typing import List


@object_type
class DaggerCi:
    @function
    async def build_and_push(
        self,
        github_token: dagger.Secret,
        github_actor: str = "andrewrothstein",
        upstream_registry: str = "ghcr.io",
        upstream_registry_path: str = "andrewrothstein",
        upstream_image_name: str = "docker-ansible",
        target_registry: str = "ghcr.io",
        target_registry_path: str = "andrewrothstein",
        target_image_name: str = "tasks",
        platform: str = "linux/amd64",
        os: str = "ubuntu",
        os_ver: str = "jammy",
    ) -> str:
        """Build and push a single platform image"""
        
        # Build the upstream and target tags
        upstream_tag = f"0.0.0-{os}.{os_ver}"
        target_tag = f"0.0.0-{os}.{os_ver}"
        
        upstream_image = f"{upstream_registry}/{upstream_registry_path}/{upstream_image_name}:{upstream_tag}"
        target_image = f"{target_registry}/{target_registry_path}/{target_image_name}:{target_tag}"
        
        # Download task binary
        downloader = (
            dag.container()
            .from_("alpine:latest")
            .with_exec(["apk", "--no-cache", "add", "ca-certificates", "curl"])
            .with_exec(["sh", "-c", "$(curl --location https://taskfile.dev/install.sh) -- -d -b /tmp"])
            .with_exec(["chmod", "+x", "/tmp/task"])
        )
        
        task_binary = downloader.file("/tmp/task")
        
        # Get the project directory
        project_dir = dag.current_module().source()
        
        # Build the main container
        container = (
            dag.container(platform=dagger.Platform(platform))
            .from_(upstream_image)
            .with_file("/tmp/task", task_binary)
            .with_directory("/tasks", project_dir)
            .with_workdir("/tasks")
            .with_exec(["/tmp/task", "-t", "ansible-local.yml"])
            .with_exec(["rm", "/tmp/task"])
            .with_label("maintainer", "Andrew Rothstein andrew.rothstein@gmail.com")
        )
        
        # Login to registry
        container = container.with_registry_auth(
            target_registry,
            github_actor,
            github_token,
        )
        
        # Publish the image
        published = await container.publish(target_image)
        
        return f"Published: {published}"
    
    @function
    async def build_all(
        self,
        github_token: dagger.Secret,
        github_actor: str = "andrewrothstein",
        matrix_file: str = "platform-matrix-v1.json",
    ) -> List[str]:
        """Build and push all platform images from the matrix"""
        
        # Read the platform matrix
        project_dir = dag.current_module().source()
        matrix_content = await project_dir.file(matrix_file).contents()
        platforms = json.loads(matrix_content)
        
        results = []
        
        for platform in platforms:
            os = platform["OS"]
            os_ver = platform["OS_VER"]
            
            # Build for both amd64 and arm64 where applicable
            # Some targets only build for amd64
            architectures = ["linux/amd64"]
            
            # Add arm64 for platforms that support it (alpine, debian, ubuntu)
            if os in ["alpine", "debian", "ubuntu"]:
                architectures.append("linux/arm64")
            
            for arch in architectures:
                try:
                    result = await self.build_and_push(
                        github_token=github_token,
                        github_actor=github_actor,
                        platform=arch,
                        os=os,
                        os_ver=os_ver,
                    )
                    results.append(f"{os}.{os_ver} ({arch}): {result}")
                except Exception as e:
                    results.append(f"{os}.{os_ver} ({arch}): ERROR - {str(e)}")
        
        return results
    
    @function
    async def build_single_matrix_entry(
        self,
        github_token: dagger.Secret,
        os: str,
        os_ver: str,
        github_actor: str = "andrewrothstein",
    ) -> List[str]:
        """Build and push images for a single matrix entry (used by GitHub Actions)"""
        
        results = []
        
        # Determine architectures based on OS
        architectures = ["linux/amd64"]
        if os in ["alpine", "debian", "ubuntu"]:
            architectures.append("linux/arm64")
        
        for arch in architectures:
            try:
                result = await self.build_and_push(
                    github_token=github_token,
                    github_actor=github_actor,
                    platform=arch,
                    os=os,
                    os_ver=os_ver,
                )
                results.append(f"{arch}: {result}")
            except Exception as e:
                results.append(f"{arch}: ERROR - {str(e)}")
        
        return results
    
    @function
    async def build_only(
        self,
        upstream_registry: str = "ghcr.io",
        upstream_registry_path: str = "andrewrothstein",
        upstream_image_name: str = "docker-ansible",
        platform: str = "linux/amd64",
        os: str = "ubuntu",
        os_ver: str = "jammy",
    ) -> str:
        """Build a single platform image without pushing (for PR validation)"""
        
        # Build the upstream tag
        upstream_tag = f"0.0.0-{os}.{os_ver}"
        upstream_image = f"{upstream_registry}/{upstream_registry_path}/{upstream_image_name}:{upstream_tag}"
        
        # Download task binary
        downloader = (
            dag.container()
            .from_("alpine:latest")
            .with_exec(["apk", "--no-cache", "add", "ca-certificates", "curl"])
            .with_exec(["sh", "-c", "$(curl --location https://taskfile.dev/install.sh) -- -d -b /tmp"])
            .with_exec(["chmod", "+x", "/tmp/task"])
        )
        
        task_binary = downloader.file("/tmp/task")
        
        # Get the project directory
        project_dir = dag.current_module().source()
        
        # Build the main container
        container = (
            dag.container(platform=dagger.Platform(platform))
            .from_(upstream_image)
            .with_file("/tmp/task", task_binary)
            .with_directory("/tasks", project_dir)
            .with_workdir("/tasks")
            .with_exec(["/tmp/task", "-t", "ansible-local.yml"])
            .with_exec(["rm", "/tmp/task"])
            .with_label("maintainer", "Andrew Rothstein andrew.rothstein@gmail.com")
        )
        
        # Export to verify build succeeds
        await container.export("/tmp/test-image.tar")
        
        return f"Build successful for {os}.{os_ver} ({platform})"
    
    @function
    async def build_single_matrix_entry_pr(
        self,
        os: str,
        os_ver: str,
    ) -> List[str]:
        """Build images for a single matrix entry without pushing (for PR validation)"""
        
        results = []
        
        # Determine architectures based on OS
        architectures = ["linux/amd64"]
        if os in ["alpine", "debian", "ubuntu"]:
            architectures.append("linux/arm64")
        
        for arch in architectures:
            try:
                result = await self.build_only(
                    platform=arch,
                    os=os,
                    os_ver=os_ver,
                )
                results.append(f"{arch}: {result}")
            except Exception as e:
                results.append(f"{arch}: ERROR - {str(e)}")
        
        return results