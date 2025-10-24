"""Command execution for bootstrap operations."""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from bootstrap.profile import BootstrapProfile

console = Console()


class ExecutionError(Exception):
    """Error during command execution."""

    pass


def run_task(
    task: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    dry_run: bool = False,
) -> tuple[int, str, str]:
    """
    Run a task command and return exit code, stdout, stderr.

    Args:
        task: Task command in format 'namespace:task' (e.g., 'kind:create')
        cwd: Working directory for command execution
        env: Additional environment variables
        dry_run: If True, only print what would be executed

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    cmd = ["task", task]

    if dry_run:
        console.print(f"[dim]Would run: {' '.join(cmd)}[/dim]")
        return (0, "", "")

    console.print(f"[blue]Running:[/blue] task {task}")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            console.print(f"[red]Failed:[/red] task {task}")
            console.print(f"[red]stderr:[/red] {result.stderr}")
            return (result.returncode, result.stdout, result.stderr)

        console.print(f"[green]✓[/green] task {task}")
        return (result.returncode, result.stdout, result.stderr)

    except Exception as e:
        console.print(f"[red]Error executing task {task}:[/red] {e}")
        return (1, "", str(e))


def execute_profile(
    profile: BootstrapProfile,
    dry_run: bool = False,
    skip_cluster: bool = False,
    progress_callback: Callable[[str], None] | None = None,
) -> bool:
    """
    Execute a bootstrap profile.

    Args:
        profile: Bootstrap profile to execute
        dry_run: If True, only print what would be executed
        skip_cluster: If True, skip cluster creation
        progress_callback: Optional callback for progress updates

    Returns:
        True if successful, False otherwise
    """
    console.print(f"\n[bold cyan]Bootstrapping:[/bold cyan] {profile.name}")
    if profile.description:
        console.print(f"[dim]{profile.description}[/dim]\n")

    # Step 1: Create cluster (if needed)
    if not skip_cluster and profile.cluster.create:
        cluster_task = f"{profile.cluster.provider}:create"
        console.print(f"\n[bold]Step 1:[/bold] Creating cluster ({profile.cluster.provider})")

        if progress_callback:
            progress_callback(f"Creating cluster: {profile.cluster.provider}")

        exit_code, _, stderr = run_task(cluster_task, dry_run=dry_run)
        if exit_code != 0:
            console.print(f"[red]✗ Failed to create cluster[/red]")
            return False
    else:
        console.print(f"\n[dim]Skipping cluster creation[/dim]")

    # Step 2: Install components sequentially
    if profile.components:
        console.print(f"\n[bold]Step 2:[/bold] Installing components")

        for i, component in enumerate(profile.components, 1):
            if progress_callback:
                progress_callback(f"Installing: {component} ({i}/{len(profile.components)})")

            exit_code, _, stderr = run_task(component, dry_run=dry_run)
            if exit_code != 0:
                console.print(f"[red]✗ Failed to install {component}[/red]")
                return False

    # Step 3: Install parallel components
    if profile.parallel_components:
        console.print(f"\n[bold]Step 3:[/bold] Installing parallel components")

        if dry_run:
            for component in profile.parallel_components:
                run_task(component, dry_run=True)
        else:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(run_task, component): component
                    for component in profile.parallel_components
                }

                for future in as_completed(futures):
                    component = futures[future]
                    try:
                        exit_code, _, stderr = future.result()
                        if exit_code != 0:
                            console.print(f"[red]✗ Failed to install {component}[/red]")
                            return False
                    except Exception as e:
                        console.print(f"[red]✗ Error installing {component}:[/red] {e}")
                        return False

    console.print(f"\n[bold green]✓ Bootstrap complete:[/bold green] {profile.name}\n")
    return True


def destroy_cluster(provider: str, dry_run: bool = False) -> bool:
    """
    Destroy a cluster.

    Args:
        provider: Cluster provider (e.g., kind, k3d)
        dry_run: If True, only print what would be executed

    Returns:
        True if successful, False otherwise
    """
    console.print(f"\n[bold yellow]Destroying cluster:[/bold yellow] {provider}")

    destroy_task = f"{provider}:delete"
    exit_code, _, stderr = run_task(destroy_task, dry_run=dry_run)

    if exit_code != 0:
        console.print(f"[red]✗ Failed to destroy cluster[/red]")
        return False

    console.print(f"[green]✓ Cluster destroyed[/green]\n")
    return True
