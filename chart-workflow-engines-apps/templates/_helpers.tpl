{{/*
An Application that installs chart-cnpg-instance from this repo.
Takes a dict with: root, name, namespace, valuesFile and optional namespaceLabels.
*/}}
{{- define "workflow-engines-apps.pg" -}}
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {{ .name }}
  namespace: {{ .root.Release.Namespace }}
  annotations:
    # databases first; the engines wait for these apps to be healthy
    argocd.argoproj.io/sync-wave: "0"
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: {{ .root.Values.project }}
  source:
    repoURL: {{ .root.Values.repoURL }}
    targetRevision: {{ .root.Values.targetRevision }}
    path: chart-cnpg-instance
    helm:
      releaseName: {{ .name }}
      valueFiles:
        - ../{{ .valuesFile }}
  destination:
    server: {{ .root.Values.destination.server }}
    namespace: {{ .namespace }}
  syncPolicy:
    {{- toYaml .root.Values.syncPolicy | nindent 4 }}
    {{- with .namespaceLabels }}
    managedNamespaceMetadata:
      labels:
        {{- toYaml . | nindent 8 }}
    {{- end }}
    syncOptions:
      - CreateNamespace=true
{{- end }}
