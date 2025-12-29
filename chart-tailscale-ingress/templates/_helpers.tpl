{{/*
Expand the name of the chart.
*/}}
{{- define "tailscale-ingress.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "tailscale-ingress.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "tailscale-ingress.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "tailscale-ingress.labels" -}}
helm.sh/chart: {{ include "tailscale-ingress.chart" . }}
{{ include "tailscale-ingress.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "tailscale-ingress.selectorLabels" -}}
app.kubernetes.io/name: {{ include "tailscale-ingress.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Construct host with subdomain.
Usage: {{ include "tailscale-ingress.host" (dict "host" .host "subdomain" $.Values.subdomain) }}
Result: <host>-<subdomain> (hyphen separator - Tailscale doesn't support dots in hostnames)
Subdomain is passed by tailscale-ingress.yml wrapper, defaulting to hostname.
If subdomain is empty, returns just the host.
*/}}
{{- define "tailscale-ingress.host" -}}
{{- if .subdomain -}}
{{- printf "%s-%s" .host .subdomain -}}
{{- else -}}
{{- .host -}}
{{- end -}}
{{- end -}}
