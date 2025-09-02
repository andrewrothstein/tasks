"""vCluster ArgoCD Enroller - Kubernetes operator for automatic vCluster enrollment in ArgoCD."""

__version__ = "0.1.0"

from .operator import (
    vcluster_created,
    vcluster_deleted,
    vcluster_resumed,
)

__all__ = [
    "vcluster_created",
    "vcluster_deleted",
    "vcluster_resumed",
]
