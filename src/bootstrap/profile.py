"""Bootstrap profile models and loader."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class ClusterConfig(BaseModel):
    """Cluster provider configuration."""

    provider: str = Field(
        description="Cluster provider (e.g., kind, kind+cilium, k3d, byo-cluster)"
    )
    create: bool = Field(default=True, description="Whether to create the cluster")


class BootstrapProfile(BaseModel):
    """Complete bootstrap profile specification."""

    name: str = Field(description="Profile name")
    description: str = Field(default="", description="Profile description")
    cluster: ClusterConfig = Field(description="Cluster configuration")
    components: list[str] = Field(
        default_factory=list,
        description="List of components to install (task namespace:task format)",
    )
    parallel_components: list[str] = Field(
        default_factory=list,
        description="Components that can be installed in parallel",
    )

    @classmethod
    def from_file(cls, path: Path) -> "BootstrapProfile":
        """Load profile from YAML file."""
        with path.open("r") as f:
            data = yaml.safe_load(f)
        return cls(**data)


def list_profiles(profiles_dir: Path = Path("profiles")) -> list[Path]:
    """List all available profile files."""
    if not profiles_dir.exists():
        return []
    return sorted(profiles_dir.glob("*.yml")) + sorted(profiles_dir.glob("*.yaml"))


def load_profile(name: str, profiles_dir: Path = Path("profiles")) -> BootstrapProfile:
    """Load a profile by name."""
    # Try with .yml first, then .yaml
    for ext in [".yml", ".yaml"]:
        profile_path = profiles_dir / f"{name}{ext}"
        if profile_path.exists():
            return BootstrapProfile.from_file(profile_path)

    available = [p.stem for p in list_profiles(profiles_dir)]
    raise FileNotFoundError(
        f"Profile '{name}' not found. Available profiles: {', '.join(available)}"
    )
