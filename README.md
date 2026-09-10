# Bedrock App

A small Flask API that calls AWS Bedrock, containerised with Docker and published
to Amazon ECR via GitHub Actions.

## Endpoints

| Method | Path       | Description                                             |
|--------|------------|---------------------------------------------------------|
| GET    | `/health`  | Liveness check. Returns `{"status": "ok"}`.             |
| POST   | `/invoke`  | Body `{"prompt": "..."}`. Calls Bedrock, returns reply. |

## Configuration

Environment variables read at runtime:

| Variable            | Default                                        | Notes                              |
|---------------------|------------------------------------------------|------------------------------------|
| `AWS_REGION`        | `eu-west-2`                                     | Region for the Bedrock client.     |
| `BEDROCK_MODEL_ID`  | `anthropic.claude-3-haiku-20240307-v1:0`        | Bedrock model to invoke.           |

AWS credentials come from the standard boto3 chain (task role, instance profile,
environment, or `~/.aws`). `/invoke` requires `bedrock:InvokeModel` permission on
the model; `/health` needs no AWS access.

## Local development (Coder)

Build and run the container locally:

```bash
docker build -t bedrock-app:local .
docker run --rm -p 8080:8080 bedrock-app:local

# In another shell:
curl localhost:8080/health
```

To exercise `/invoke` locally, pass AWS credentials into the container, e.g.:

```bash
docker run --rm -p 8080:8080 \
  -e AWS_REGION=eu-west-2 \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
  bedrock-app:local

curl -X POST localhost:8080/invoke \
  -H 'content-type: application/json' \
  -d '{"prompt": "Hello"}'
```

### Build and push from your workspace

`build-and-push.sh` mirrors the CI pipeline for manual pushes:

```bash
export AWS_REGION=eu-west-2
export ECR_REPOSITORY=bedrock-app
./build-and-push.sh
```

It creates the ECR repo if missing, logs Docker in to ECR, then builds and pushes
`:<git-sha>` and `:latest`.

## Automated publish (GitHub Actions)

`.github/workflows/ecr-push.yml` builds and pushes on every push to `main` and on
`v*` tags. It authenticates to AWS with **OIDC** — no long-lived access keys stored
in GitHub.

### One-time AWS setup

1. **ECR repository**

   ```bash
   aws ecr create-repository --repository-name bedrock-app --region eu-west-2
   ```

2. **GitHub OIDC identity provider** (once per account)

   ```bash
   aws iam create-open-id-connect-provider \
     --url https://token.actions.githubusercontent.com \
     --client-id-list sts.amazonaws.com \
     --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
   ```

3. **IAM role** the workflow assumes. Trust policy (replace `ACCOUNT`, `ORG/REPO`):

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Principal": { "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com" },
       "Action": "sts:AssumeRoleWithWebIdentity",
       "Condition": {
         "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
         "StringLike": { "token.actions.githubusercontent.com:sub": "repo:ORG/REPO:*" }
       }
     }]
   }
   ```

   Attach a permissions policy allowing ECR push:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       { "Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*" },
       { "Effect": "Allow",
         "Action": [
           "ecr:BatchCheckLayerAvailability",
           "ecr:InitiateLayerUpload",
           "ecr:UploadLayerPart",
           "ecr:CompleteLayerUpload",
           "ecr:PutImage"
         ],
         "Resource": "arn:aws:ecr:eu-west-2:ACCOUNT:repository/bedrock-app" }
     ]
   }
   ```

### GitHub repository settings

- **Variables:** `AWS_REGION` (e.g. `eu-west-2`), `ECR_REPOSITORY` (e.g. `bedrock-app`)
- **Secret:** `AWS_ROLE_ARN` — ARN of the role created above

Push to `main` and the image lands in ECR tagged with the commit SHA and `latest`.

## Production note

The container runs Flask's built-in development server, which is fine for this beta.
For production, front the app with a WSGI server such as `gunicorn`.
