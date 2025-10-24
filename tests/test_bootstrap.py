"""Tests for bootstrap tool."""

from pathlib import Path

import pytest

from bootstrap.profile import BootstrapProfile, ClusterConfig, load_profile, list_profiles


def test_cluster_config():
    """Test ClusterConfig model."""
    config = ClusterConfig(provider="kind+cilium")
    assert config.provider == "kind+cilium"
    assert config.create is True

    config = ClusterConfig(provider="byo-cluster", create=False)
    assert config.provider == "byo-cluster"
    assert config.create is False


def test_bootstrap_profile():
    """Test BootstrapProfile model."""
    profile = BootstrapProfile(
        name="test",
        description="Test profile",
        cluster=ClusterConfig(provider="kind"),
        components=["metrics-server:upgrade"],
        parallel_components=["prometheus:upgrade"],
    )

    assert profile.name == "test"
    assert profile.description == "Test profile"
    assert profile.cluster.provider == "kind"
    assert len(profile.components) == 1
    assert len(profile.parallel_components) == 1


def test_load_profile(tmp_path: Path):
    """Test loading profile from file."""
    profile_content = """name: test-profile
description: Test description
cluster:
  provider: kind+cilium
  create: true
components:
  - metrics-server:upgrade
  - cert-manager:upgrade
parallel_components:
  - prometheus:upgrade
"""

    profile_file = tmp_path / "test-profile.yml"
    profile_file.write_text(profile_content)

    profile = BootstrapProfile.from_file(profile_file)

    assert profile.name == "test-profile"
    assert profile.description == "Test description"
    assert profile.cluster.provider == "kind+cilium"
    assert len(profile.components) == 2
    assert len(profile.parallel_components) == 1


def test_list_profiles():
    """Test listing available profiles."""
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        pytest.skip("profiles directory doesn't exist")

    profiles = list_profiles(profiles_dir)
    assert isinstance(profiles, list)

    if profiles:
        # Should be sorted
        assert profiles == sorted(profiles)


def test_load_profile_by_name():
    """Test loading profile by name."""
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        pytest.skip("profiles directory doesn't exist")

    profiles = list_profiles(profiles_dir)
    if not profiles:
        pytest.skip("no profiles available")

    # Load first profile
    profile_name = profiles[0].stem
    profile = load_profile(profile_name, profiles_dir)

    assert profile.name is not None
    assert profile.cluster.provider is not None


def test_load_nonexistent_profile(tmp_path: Path):
    """Test loading a profile that doesn't exist."""
    with pytest.raises(FileNotFoundError, match="Profile.*not found"):
        load_profile("nonexistent", tmp_path)
