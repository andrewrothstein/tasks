"""Pytest configuration and fixtures for vcluster-argocd-enroller tests."""

import pytest
import subprocess
import time
import uuid
from kubernetes import client, config
from pathlib import Path


@pytest.fixture(scope="session")
def k8s_client():
    """Initialize Kubernetes client."""
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    return {
        "core_v1": client.CoreV1Api(),
        "apps_v1": client.AppsV1Api(),
    }


@pytest.fixture(scope="session")
def test_namespace():
    """Create a test namespace for the session."""
    namespace = f"vcluster-test-{uuid.uuid4().hex[:8]}"

    # Create namespace
    subprocess.run([
        "kubectl", "create", "namespace", namespace
    ], check=True)

    yield namespace

    # Cleanup namespace
    subprocess.run([
        "kubectl", "delete", "namespace", namespace, "--ignore-not-found=true"
    ], check=False)


@pytest.fixture
def vcluster_name():
    """Generate a unique vcluster name for each test."""
    return f"test-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def create_vcluster(test_namespace, vcluster_name):
    """Create a vcluster for testing."""
    def _create(name=None, namespace=None):
        name = name or vcluster_name
        namespace = namespace or test_namespace

        # Create vcluster
        result = subprocess.run([
            "vcluster", "create", name,
            "--namespace", namespace,
            "--distro", "k3s"
        ], capture_output=True, text=True)

        if result.returncode != 0:
            pytest.fail(f"Failed to create vcluster: {result.stderr}")

        # Wait for vcluster to be ready
        time.sleep(20)

        return name, namespace

    created_vclusters = []

    def _create_and_track(*args, **kwargs):
        vcluster_info = _create(*args, **kwargs)
        created_vclusters.append(vcluster_info)
        return vcluster_info

    yield _create_and_track

    # Cleanup all created vclusters
    for name, namespace in created_vclusters:
        subprocess.run([
            "vcluster", "delete", name,
            "--namespace", namespace
        ], check=False)


@pytest.fixture
def operator_process():
    """Run the operator in a subprocess."""
    processes = []

    def _start_operator(namespace=None, verbose=True):
        cmd = ["uv", "run", "vcluster-argocd-enroller"]
        if namespace:
            cmd.extend(["--namespace", namespace])
        if verbose:
            cmd.append("--verbose")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(process)

        # Give operator time to start
        time.sleep(5)

        return process

    yield _start_operator

    # Cleanup: terminate all operator processes
    for process in processes:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.fixture
def wait_for_condition():
    """Helper to wait for a condition with timeout."""
    def _wait(condition_func, timeout=30, interval=2, message="Condition not met"):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        pytest.fail(f"Timeout waiting for condition: {message}")

    return _wait
