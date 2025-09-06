# Terraform (GCP) Bootstrap
This creates a GCS bucket you can use for data/artifacts.
```bash
terraform init
terraform apply -var="project_id=YOUR_PROJECT" -var="bucket_name=YOUR_BUCKET"
```
