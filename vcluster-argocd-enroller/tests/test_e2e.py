#!/usr/bin/env python3
"""
End-to-end test for vCluster ArgoCD Enroller operator.
This test requires a real Kubernetes cluster with ArgoCD installed.
"""

import pytest
import subprocess
import time
import tempfile
import os
from pathlib import Path
from kubernetes import client, config


# Skip these tests by default, run with: pytest -m e2e
pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def k8s_client():
    """Initialize Kubernetes client."""
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()

    return client.CoreV1Api(), client.AppsV1Api()


@pytest.fixture(scope="module")
def test_namespace():
    """Create and cleanup test namespace."""
    namespace = f"vcluster-test-{int(time.time())}"

    v1 = client.CoreV1Api()

    # Create namespace
    v1.create_namespace(
        body=client.V1Namespace(
            metadata=client.V1ObjectMeta(name=namespace)
        )
    )

    yield namespace

    # Cleanup namespace
    try:
        v1.delete_namespace(name=namespace)
    except client.exceptions.ApiException:
        pass


@pytest.fixture
def operator_process(test_namespace):
    """Start operator process for the test."""
    proc = subprocess.Popen(
        ["uv", "run", "vcluster-argocd-enroller", "--namespace", test_namespace],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Give operator time to start
    time.sleep(5)

    yield proc

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


class TestE2EOperator:
    """End-to-end tests for the operator."""

    @pytest.mark.slow
    def test_automatic_enrollment_and_cleanup(self, k8s_client, test_namespace, operator_process):
        """Test full lifecycle: create vcluster, verify enrollment, delete, verify cleanup."""
        core_v1, apps_v1 = k8s_client
        vcluster_name = f"e2e-test-{int(time.time())}"

        # Step 1: Create vCluster
        result = subprocess.run(
            ["vcluster", "create", vcluster_name, "--namespace", test_namespace],
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0, f"Failed to create vcluster: {result.stderr}"

        # Step 2: Wait for vCluster to be ready
        max_wait = 60
        start = time.time()
        while time.time() - start < max_wait:
            try:
                # Check if vcluster secret exists
                secret = core_v1.read_namespaced_secret(
                    name=f"vc-{vcluster_name}",
                    namespace=test_namespace
                )
                if secret:
                    break
            except client.exceptions.ApiException:
                pass
            time.sleep(5)
        else:
            pytest.fail(f"vCluster secret not created within {max_wait} seconds")

        # Step 3: Wait for operator to create ArgoCD secret
        argocd_secret_name = f"vcluster-{vcluster_name}"
        start = time.time()
        while time.time() - start < 30:
            try:
                secret = core_v1.read_namespaced_secret(
                    name=argocd_secret_name,
                    namespace="argocd"
                )
                # Verify labels
                assert secret.metadata.labels.get("argocd.argoproj.io/secret-type") == "cluster"
                assert secret.metadata.labels.get("vcluster-operator") == "true"
                break
            except client.exceptions.ApiException:
                pass
            time.sleep(2)
        else:
            pytest.fail("ArgoCD secret not created within 30 seconds")

        # Step 4: Delete vCluster
        result = subprocess.run(
            ["vcluster", "delete", vcluster_name, "--namespace", test_namespace],
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result.returncode == 0, f"Failed to delete vcluster: {result.stderr}"

        # Step 5: Verify ArgoCD secret is removed
        time.sleep(10)  # Give operator time to process deletion

        with pytest.raises(client.exceptions.ApiException) as exc:
            core_v1.read_namespaced_secret(
                name=argocd_secret_name,
                namespace="argocd"
            )
        assert exc.value.status == 404, "ArgoCD secret was not removed"

    def test_multiple_vclusters(self, k8s_client, test_namespace, operator_process):
        """Test operator handles multiple vClusters correctly."""
        core_v1, apps_v1 = k8s_client
        vcluster_names = [f"multi-{i}-{int(time.time())}" for i in range(2)]

        try:
            # Create multiple vClusters
            for name in vcluster_names:
                result = subprocess.run(
                    ["vcluster", "create", name, "--namespace", test_namespace],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                assert result.returncode == 0

            # Wait and verify all ArgoCD secrets are created
            time.sleep(30)

            for name in vcluster_names:
                secret = core_v1.read_namespaced_secret(
                    name=f"vcluster-{name}",
                    namespace="argocd"
                )
                assert secret.metadata.labels.get("vcluster-operator") == "true"

        finally:
            # Cleanup
            for name in vcluster_names:
                subprocess.run(
                    ["vcluster", "delete", name, "--namespace", test_namespace],
                    capture_output=True,
                    timeout=60
                )


@pytest.mark.parametrize("statefulset_name,expected_vcluster_name", [
    ("test-cluster", "test-cluster"),
    ("vcluster-test-cluster", "test-cluster"),
    ("my-app", "my-app"),
    ("vcluster-my-app", "my-app"),
])
def test_name_extraction(statefulset_name, expected_vcluster_name):
    """Test vcluster name extraction from StatefulSet names."""
    from vcluster_argocd_enroller.operator import vc_name
    assert vc_name(statefulset_name) == expected_vcluster_name
