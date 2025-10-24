"""CLI interface for bootstrap tool."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from bootstrap.executor import destroy_cluster, execute_profile
from bootstrap.profile import list_profiles, load_profile

console = Console()


@click.group()
@click.version_option()
def main() -> None:
    """Kubernetes cluster bootstrap tool.

    Manage independent bootstrap profiles for different cluster configurations.
    """
    pass


@main.command()
@click.argument("profile_name")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be executed without running commands",
)
@click.option(
    "--skip-cluster",
    is_flag=True,
    help="Skip cluster creation (use existing cluster)",
)
@click.option(
    "--profiles-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("profiles"),
    help="Directory containing profile definitions",
)
def apply(
    profile_name: str,
    dry_run: bool,
    skip_cluster: bool,
    profiles_dir: Path,
) -> None:
    """Apply a bootstrap profile to create and configure a cluster.

    PROFILE_NAME: Name of the profile to apply (without .yml extension)

    Examples:

        bootstrap apply kind-minimal

        bootstrap apply k3d-dev --dry-run

        bootstrap apply kind-full --skip-cluster
    """
    try:
        profile = load_profile(profile_name, profiles_dir)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    success = execute_profile(profile, dry_run=dry_run, skip_cluster=skip_cluster)

    if not success:
        console.print("[red]Bootstrap failed[/red]")
        sys.exit(1)

    console.print("[green]Bootstrap succeeded[/green]")


@main.command()
@click.option(
    "--profiles-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("profiles"),
    help="Directory containing profile definitions",
)
def list(profiles_dir: Path) -> None:
    """List all available bootstrap profiles."""
    profiles = list_profiles(profiles_dir)

    if not profiles:
        console.print(f"[yellow]No profiles found in {profiles_dir}[/yellow]")
        console.print("\nCreate a profile in the profiles/ directory to get started.")
        return

    table = Table(title="Available Bootstrap Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Cluster Provider", style="blue")
    table.add_column("Components", style="green")
    table.add_column("Description", style="dim")

    for profile_path in profiles:
        try:
            profile = load_profile(profile_path.stem, profiles_dir)
            component_count = len(profile.components) + len(profile.parallel_components)
            table.add_row(
                profile.name,
                profile.cluster.provider,
                str(component_count),
                profile.description,
            )
        except Exception as e:
            table.add_row(
                profile_path.stem,
                "[red]Error[/red]",
                "",
                f"[red]Failed to load: {e}[/red]",
            )

    console.print(table)


@main.command()
@click.argument("profile_name")
@click.option(
    "--profiles-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("profiles"),
    help="Directory containing profile definitions",
)
def show(profile_name: str, profiles_dir: Path) -> None:
    """Show details of a specific bootstrap profile.

    PROFILE_NAME: Name of the profile to show
    """
    try:
        profile = load_profile(profile_name, profiles_dir)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    console.print(f"\n[bold cyan]{profile.name}[/bold cyan]")
    if profile.description:
        console.print(f"[dim]{profile.description}[/dim]")

    console.print(f"\n[bold]Cluster:[/bold]")
    console.print(f"  Provider: {profile.cluster.provider}")
    console.print(f"  Create: {profile.cluster.create}")

    if profile.components:
        console.print(f"\n[bold]Components (sequential):[/bold]")
        for i, component in enumerate(profile.components, 1):
            console.print(f"  {i}. {component}")

    if profile.parallel_components:
        console.print(f"\n[bold]Components (parallel):[/bold]")
        for component in profile.parallel_components:
            console.print(f"  • {component}")

    console.print()


@main.command()
@click.argument("provider")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be executed without running commands",
)
def destroy(provider: str, dry_run: bool) -> None:
    """Destroy a cluster.

    PROVIDER: Cluster provider (e.g., kind, kind+cilium, k3d)

    Examples:

        bootstrap destroy kind

        bootstrap destroy k3d --dry-run
    """
    if not dry_run:
        click.confirm(
            f"Are you sure you want to destroy the {provider} cluster?",
            abort=True,
        )

    success = destroy_cluster(provider, dry_run=dry_run)

    if not success:
        console.print("[red]Destroy failed[/red]")
        sys.exit(1)


@main.command()
def init() -> None:
    """Initialize profiles directory with example profiles."""
    profiles_dir = Path("profiles")
    profiles_dir.mkdir(exist_ok=True)

    example_profiles = {
        "kind-minimal.yml": """name: kind-minimal
description: Minimal Kind cluster with Cilium and basic monitoring
cluster:
  provider: kind+cilium
  create: true
components:
  - metrics-server:upgrade
  - cert-manager:upgrade
""",
        "kind-full.yml": """name: kind-full
description: Full-featured Kind cluster with complete stack
cluster:
  provider: kind+cilium
  create: true
components:
  - metrics-server:upgrade
  - cert-manager:upgrade
  - gateway-api:apply
  - metallb:upgrade
  - argocd:upgrade
parallel_components:
  - kube-prometheus-stack:upgrade
  - loki:upgrade
""",
        "k3d-dev.yml": """name: k3d-dev
description: K3d cluster for development
cluster:
  provider: k3d
  create: true
components:
  - metrics-server:upgrade
  - argocd:upgrade
""",
        "byo-observability.yml": """name: byo-observability
description: Install observability stack on existing cluster
cluster:
  provider: byo-cluster
  create: false
components:
  - metrics-server:upgrade
parallel_components:
  - kube-prometheus-stack:upgrade
  - grafana:upgrade
  - kiali:upgrade
""",
    }

    created = []
    for filename, content in example_profiles.items():
        profile_path = profiles_dir / filename
        if profile_path.exists():
            console.print(f"[yellow]Skipping:[/yellow] {filename} (already exists)")
        else:
            profile_path.write_text(content)
            created.append(filename)
            console.print(f"[green]Created:[/green] {filename}")

    if created:
        console.print(f"\n[green]✓[/green] Created {len(created)} example profiles")
        console.print("\nUsage:")
        console.print("  bootstrap list")
        console.print("  bootstrap show kind-minimal")
        console.print("  bootstrap apply kind-minimal")
    else:
        console.print("\n[yellow]All example profiles already exist[/yellow]")


if __name__ == "__main__":
    main()
