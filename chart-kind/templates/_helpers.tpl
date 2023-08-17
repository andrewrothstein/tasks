{{- define "kind.node" -}}
image: "kindest/node:v{{ .k8sVer }}@{{ dig .kindVer .k8sVer "latest" .nodeImageSHAs }}"
{{- if .extraMounts -}}
extraMounts:
  {{- toYaml .extraMounts | nindent 2 }}
{{- end -}}
{{- end }}