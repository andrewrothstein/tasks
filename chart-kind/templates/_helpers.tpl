{{- define "kind.node" -}}
image: "kindest/node:v{{ .k8sVer }}@{{ dig .kindVer .k8sVer "latest" .nodeImageSHAs }}"
{{- with .extraMounts }}
extraMounts:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}