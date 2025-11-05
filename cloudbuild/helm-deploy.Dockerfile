# Custom Cloud Build image with Helm, Helmfile, and deployment tools
# Used for deploying to GKE in CI/CD pipelines
#
# Build and push:
#   gcloud builds submit --config=cloudbuild/build-helm-image.yaml cloudbuild/

FROM gcr.io/google.com/cloudsdktool/cloud-sdk:alpine

# Install system dependencies
RUN apk add --no-cache \
    bash \
    curl \
    wget \
    git \
    jq \
    ca-certificates

# Install kubectl (latest)
RUN gcloud components install kubectl --quiet

# Install Helm
RUN curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install Helmfile
ARG HELMFILE_VERSION=0.162.0
RUN wget -q -O /usr/local/bin/helmfile \
    https://github.com/helmfile/helmfile/releases/download/v${HELMFILE_VERSION}/helmfile_linux_amd64 && \
    chmod +x /usr/local/bin/helmfile

# Install Helm plugins
RUN helm plugin install https://github.com/databus23/helm-diff --version v3.9.4

# Install yq for YAML processing
ARG YQ_VERSION=4.40.5
RUN wget -q -O /usr/local/bin/yq \
    https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64 && \
    chmod +x /usr/local/bin/yq

# Verify installations
RUN gcloud --version && \
    kubectl version --client && \
    helm version && \
    helmfile version && \
    yq --version

# Set working directory
WORKDIR /workspace

# Default entrypoint
ENTRYPOINT ["bash"]
