#!/usr/bin/env bash
#
# Local build + push to Amazon ECR, mirroring the GitHub Actions pipeline.
# Use during Coder development to validate the image before CI publishes it.
#
# Required environment variables:
#   AWS_REGION       e.g. eu-west-2
#   ECR_REPOSITORY   ECR repo name, e.g. bedrock-app
# Optional:
#   IMAGE_TAG        defaults to the short git SHA (or "local" outside git)
#
# AWS credentials are taken from the ambient environment (Coder workspace role,
# `aws configure`, SSO, or exported keys).

set -euo pipefail

: "${AWS_REGION:?set AWS_REGION}"
: "${ECR_REPOSITORY:?set ECR_REPOSITORY}"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo local)}"
IMAGE="${REGISTRY}/${ECR_REPOSITORY}"

echo "==> Ensuring ECR repository exists"
aws ecr describe-repositories --repository-names "${ECR_REPOSITORY}" --region "${AWS_REGION}" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "${ECR_REPOSITORY}" --region "${AWS_REGION}" >/dev/null

echo "==> Authenticating Docker to ECR"
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${REGISTRY}"

echo "==> Building ${IMAGE}:${IMAGE_TAG}"
docker build -t "${IMAGE}:${IMAGE_TAG}" -t "${IMAGE}:latest" .

echo "==> Pushing"
docker push "${IMAGE}:${IMAGE_TAG}"
docker push "${IMAGE}:latest"

echo "==> Done: ${IMAGE}:${IMAGE_TAG}"
