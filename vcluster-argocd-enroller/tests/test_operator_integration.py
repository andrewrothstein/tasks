#!/usr/bin/env python3
"""
Integration tests for vCluster ArgoCD Enroller operator using kopf.testing.
"""

import pytest
import kopf.testing
from unittest.mock import MagicMock, patch, Mock
import base64
import json

from vcluster_argocd_enroller import operator


@pytest.fixture
def k8s_mocked():
    """Mock Kubernetes API clients."""
    with patch('vcluster_argocd_enroller.operator.core_v1_api') as mock_core, \
         patch('vcluster_argocd_enroller.operator.apps_v1_api') as mock_apps:
        yield mock_core, mock_apps


def create_vcluster_statefulset(name="test-cluster", namespace="vcluster-test"):
    """Create a mock vCluster StatefulSet resource."""
    return {
        'apiVersion': 'apps/v1',
        'kind': 'StatefulSet',
        'metadata': {
            'name': name,
            'namespace': namespace,
            'labels': {
                'app': 'vcluster',
                'release': name
            },
            'uid': 'test-uid-12345',
        },
        'spec': {
            'replicas': 1,
            'selector': {'matchLabels': {'app': 'vcluster'}},
        }
    }


def create_vcluster_secret(name="test-cluster", namespace="vcluster-test"):
    """Create a mock vCluster secret with kubeconfig data."""
    return Mock(
        data={
            'certificate-authority': base64.b64encode(b'fake-ca-data').decode('utf-8'),
            'client-certificate': base64.b64encode(b'fake-cert-data').decode('utf-8'),
            'client-key': base64.b64encode(b'fake-key-data').decode('utf-8'),
        }
    )


class TestOperatorHandlers:
    """Test the operator handlers using kopf.testing."""

    def test_vcluster_created_handler(self, k8s_mocked):
        """Test that vcluster creation triggers ArgoCD enrollment."""
        mock_core, mock_apps = k8s_mocked

        # Setup mock to return vcluster secret
        vcluster_secret = create_vcluster_secret()
        mock_core.read_namespaced_secret.return_value = vcluster_secret

        # Create StatefulSet resource
        statefulset = create_vcluster_statefulset()

        with kopf.testing.KopfRunner(
            ['run', '-m', 'vcluster_argocd_enroller.operator', '--standalone'],
            timeout=10
        ) as runner:
            # Trigger creation event
            result = operator.vcluster_created(
                name=statefulset['metadata']['name'],
                namespace=statefulset['metadata']['namespace'],
                meta=statefulset['metadata'],
                spec=statefulset['spec']
            )

            # Verify secret was read
            mock_core.read_namespaced_secret.assert_called_once_with(
                name='vc-test-cluster',
                namespace='vcluster-test'
            )

            # Verify ArgoCD secret was created
            mock_core.create_namespaced_secret.assert_called_once()
            call_args = mock_core.create_namespaced_secret.call_args

            assert call_args[0][0] == 'argocd'  # namespace
            secret_body = call_args[0][1]

            # Verify secret structure
            assert secret_body['metadata']['name'] == 'vcluster-test-cluster'
            assert secret_body['metadata']['namespace'] == 'argocd'
            assert 'argocd.argoproj.io/secret-type' in secret_body['metadata']['labels']
            assert secret_body['metadata']['labels']['argocd.argoproj.io/secret-type'] == 'cluster'
            assert secret_body['metadata']['labels']['vcluster-operator'] == 'true'

            # Verify secret data
            assert 'name' in secret_body['data']
            assert 'server' in secret_body['data']
            assert 'config' in secret_body['data']

            assert result == {'status': 'Success'}

    def test_vcluster_deleted_handler(self, k8s_mocked):
        """Test that vcluster deletion triggers ArgoCD cleanup."""
        mock_core, mock_apps = k8s_mocked

        # Create StatefulSet resource
        statefulset = create_vcluster_statefulset()

        with kopf.testing.KopfRunner(
            ['run', '-m', 'vcluster_argocd_enroller.operator', '--standalone'],
            timeout=10
        ) as runner:
            # Trigger deletion event
            result = operator.vcluster_deleted(
                name=statefulset['metadata']['name'],
                namespace=statefulset['metadata']['namespace']
            )

            # Verify ArgoCD secret was deleted
            mock_core.delete_namespaced_secret.assert_called_once_with(
                name='vcluster-test-cluster',
                namespace='argocd'
            )

            assert result == {'status': 'Success'}

    def test_vcluster_with_prefix_name(self, k8s_mocked):
        """Test handling of vcluster with 'vcluster-' prefix in StatefulSet name."""
        mock_core, mock_apps = k8s_mocked

        # Setup mock to return vcluster secret
        vcluster_secret = create_vcluster_secret()
        mock_core.read_namespaced_secret.return_value = vcluster_secret

        # Create StatefulSet with prefixed name
        statefulset = create_vcluster_statefulset(name="vcluster-my-cluster")

        result = operator.vcluster_created(
            name=statefulset['metadata']['name'],
            namespace=statefulset['metadata']['namespace'],
            meta=statefulset['metadata'],
            spec=statefulset['spec']
        )

        # Should look for secret without the prefix
        mock_core.read_namespaced_secret.assert_called_once_with(
            name='vc-my-cluster',
            namespace='vcluster-test'
        )

        # ArgoCD secret should be created with correct name
        call_args = mock_core.create_namespaced_secret.call_args
        secret_body = call_args[0][1]
        assert secret_body['metadata']['name'] == 'vcluster-my-cluster'

    def test_missing_vcluster_secret_temporary_error(self, k8s_mocked):
        """Test that missing vcluster secret causes temporary retry."""
        mock_core, mock_apps = k8s_mocked

        # Setup mock to simulate missing secret
        from kubernetes.client.rest import ApiException
        mock_core.read_namespaced_secret.side_effect = ApiException(status=404)

        statefulset = create_vcluster_statefulset()

        # Should raise TemporaryError for retry
        with pytest.raises(kopf.TemporaryError) as exc_info:
            operator.vcluster_created(
                name=statefulset['metadata']['name'],
                namespace=statefulset['metadata']['namespace'],
                meta=statefulset['metadata'],
                spec=statefulset['spec']
            )

        assert "Failed to enroll vcluster" in str(exc_info.value)
        assert exc_info.value.delay == 60  # Should retry after 60 seconds

    def test_argocd_secret_already_deleted(self, k8s_mocked):
        """Test graceful handling when ArgoCD secret is already deleted."""
        mock_core, mock_apps = k8s_mocked

        # Setup mock to simulate already deleted secret
        from kubernetes.client.rest import ApiException
        mock_core.delete_namespaced_secret.side_effect = ApiException(status=404)

        statefulset = create_vcluster_statefulset()

        # Should handle 404 gracefully
        result = operator.vcluster_deleted(
            name=statefulset['metadata']['name'],
            namespace=statefulset['metadata']['namespace']
        )

        # Should still succeed
        assert result is None  # Returns None on 404

    def test_malformed_vcluster_secret(self, k8s_mocked):
        """Test handling of malformed vcluster secret."""
        mock_core, mock_apps = k8s_mocked

        # Setup mock with malformed secret (missing required fields)
        bad_secret = Mock(data={'some-field': 'value'})
        mock_core.read_namespaced_secret.return_value = bad_secret

        statefulset = create_vcluster_statefulset()

        # Should raise PermanentError for malformed secret
        with pytest.raises(kopf.PermanentError) as exc_info:
            operator.vcluster_created(
                name=statefulset['metadata']['name'],
                namespace=statefulset['metadata']['namespace'],
                meta=statefulset['metadata'],
                spec=statefulset['spec']
            )

        assert "Failed to parse vcluster secret" in str(exc_info.value)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_vc_name_without_prefix(self):
        """Test vcluster name extraction without prefix."""
        assert operator.vc_name("my-cluster") == "my-cluster"
        assert operator.vc_name("test-123") == "test-123"

    def test_vc_name_with_prefix(self):
        """Test vcluster name extraction with vcluster- prefix."""
        assert operator.vc_name("vcluster-my-cluster") == "my-cluster"
        assert operator.vc_name("vcluster-test-123") == "test-123"

    def test_ar_secret_name(self):
        """Test ArgoCD secret name generation."""
        assert operator.ar_secret_name("my-cluster") == "vcluster-my-cluster"
        assert operator.ar_secret_name("test") == "vcluster-test"

    def test_encode_decode(self):
        """Test base64 encoding/decoding functions."""
        test_string = "test-data-123"
        encoded = operator.encode(test_string)
        decoded = operator.decode(encoded)
        assert decoded == test_string

        # Test with special characters
        special = "https://test.example.com:8443/api"
        assert operator.decode(operator.encode(special)) == special
