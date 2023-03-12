{{- define "kind.node" -}}
{{- if .extraMounts -}}
extraMounts:
  {{- toYaml .extraMounts | nindent 2 }}
{{- end -}}

{{- end }}
