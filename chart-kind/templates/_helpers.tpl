{{- define "kind.node" -}}
{{- if .image -}}
image: {{ .image }}
{{- end }}
{{- if .extraMounts -}}
extraMounts:
  {{- toYaml .extraMounts | nindent 2 }}
{{- end -}}
{{- end }}