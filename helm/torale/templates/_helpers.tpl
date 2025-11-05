{{/*
Expand the name of the chart.
*/}}
{{- define "torale.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "torale.fullname" -}}
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
{{- define "torale.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "torale.labels" -}}
helm.sh/chart: {{ include "torale.chart" . }}
{{ include "torale.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "torale.selectorLabels" -}}
app.kubernetes.io/name: {{ include "torale.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
API specific labels
*/}}
{{- define "torale.api.labels" -}}
{{ include "torale.labels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
API selector labels
*/}}
{{- define "torale.api.selectorLabels" -}}
{{ include "torale.selectorLabels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Worker specific labels
*/}}
{{- define "torale.worker.labels" -}}
{{ include "torale.labels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
Worker selector labels
*/}}
{{- define "torale.worker.selectorLabels" -}}
{{ include "torale.selectorLabels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
Frontend specific labels
*/}}
{{- define "torale.frontend.labels" -}}
{{ include "torale.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "torale.frontend.selectorLabels" -}}
{{ include "torale.selectorLabels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "torale.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "torale.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Database URL
*/}}
{{- define "torale.databaseUrl" -}}
postgresql://{{ .Values.database.user }}:$(DB_PASSWORD)@{{ .Values.database.host }}:{{ .Values.database.port }}/{{ .Values.database.name }}
{{- end }}

{{/*
API image
*/}}
{{- define "torale.api.image" -}}
{{ .Values.image.registry }}/{{ .Values.image.repository }}/{{ .Values.api.image.name }}:{{ .Values.image.tag | default .Chart.AppVersion }}
{{- end }}

{{/*
Worker image
*/}}
{{- define "torale.worker.image" -}}
{{ .Values.image.registry }}/{{ .Values.image.repository }}/{{ .Values.worker.image.name }}:{{ .Values.image.tag | default .Chart.AppVersion }}
{{- end }}

{{/*
Frontend image
*/}}
{{- define "torale.frontend.image" -}}
{{ .Values.image.registry }}/{{ .Values.image.repository }}/{{ .Values.frontend.image.name }}:{{ .Values.image.tag | default .Chart.AppVersion }}
{{- end }}
