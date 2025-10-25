# 1. Prepare your project

- Make sure you have a GCP project:
```bash
gcloud projects list
```

- Set your project:
```bash
gcloud config set project <PROJECT_ID>
```

- Enable required services:
```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
```

# 2. Push Docker image to Artifact Registry

- Create a Docker repository:

```bash
gcloud artifacts repositories create chroma-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Chroma Docker images"
```

- Authenticate Docker with Artifact Registry:

```bash
gcloud auth configure-docker us-docker.pkg.dev
```

- Pull the official Chroma image:

```bash
docker pull chromadb/chroma:latest
```

- Tag it for Artifact Registry:

```bash
docker tag chromadb/chroma:latest \
  us-docker.pkg.dev/<PROJECT_ID>/chroma-repo/chroma-loan-navigator:latest
```

- Push the image:

```bash
docker push us-docker.pkg.dev/<PROJECT_ID>/chroma-repo/chroma-loan-navigator:latest
```

# 3. Deploy to Cloud Run

```bash
gcloud run deploy chroma-service \
  --image us-docker.pkg.dev/<PROJECT_ID>/chroma-repo/chroma-loan-navigator:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi
```
# 4. Notes:

```--allow-unauthenticated```  → public access for testing; remove in production.

```--port 8000``` → must match the Chroma server’s port.

```--memory 2Gi``` → recommended for Chroma server, can adjust.

# 5. Set Environment Variables (Optional)

 - If you want persistent storage on Cloud Run: Cloud Run doesn’t have persistent disks, so use a Cloud Storage bucket instead.

- Chroma can persist collections locally inside /data, then you can sync it to GCS periodically.

- Example with environment variables:

```bash
gcloud run services update chroma-service \
  --update-env-vars CHROMA_PERSIST_DIRECTORY=/data,CHROMA_ANONYMIZED_TELEMETRY=false
```