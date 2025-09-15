#!/bin/bash

# FinCompliance RAG Portal - Kubernetes Deployment Script
# This script deploys the application to Google Kubernetes Engine (GKE)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}"
CLUSTER_NAME="${GKE_CLUSTER_NAME:-fincompliance-cluster}"
ZONE="${GKE_ZONE:-us-central1-a}"
REGION="${GKE_REGION:-us-central1}"
NAMESPACE="${K8S_NAMESPACE:-fincompliance}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    # Check if kustomize is installed
    if ! command -v kustomize &> /dev/null; then
        log_warning "kustomize is not installed. Installing via kubectl..."
        kubectl kustomize --help > /dev/null 2>&1 || {
            log_error "kustomize is not available. Please install it first."
            exit 1
        }
    fi
    
    log_success "Prerequisites check passed"
}

authenticate_gcp() {
    log_info "Authenticating with Google Cloud..."
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Get credentials for the cluster
    gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE --project $PROJECT_ID
    
    log_success "GCP authentication completed"
}

build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    # Build image
    docker build -t gcr.io/$PROJECT_ID/fincompliance-rag-portal:$IMAGE_TAG .
    
    # Push image
    docker push gcr.io/$PROJECT_ID/fincompliance-rag-portal:$IMAGE_TAG
    
    log_success "Image built and pushed successfully"
}

deploy_to_k8s() {
    log_info "Deploying to Kubernetes..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy using kustomize
    if [ "$ENVIRONMENT" = "prod" ]; then
        kubectl apply -k k8s/overlays/prod/
    else
        kubectl apply -k k8s/overlays/dev/
    fi
    
    log_success "Deployment completed"
}

wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    
    # Wait for API deployment
    kubectl wait --for=condition=available --timeout=300s deployment/fincompliance-api -n $NAMESPACE
    
    # Wait for UI deployment
    kubectl wait --for=condition=available --timeout=300s deployment/fincompliance-ui -n $NAMESPACE
    
    log_success "Deployment is ready"
}

show_status() {
    log_info "Deployment status:"
    
    echo ""
    echo "Pods:"
    kubectl get pods -n $NAMESPACE
    
    echo ""
    echo "Services:"
    kubectl get services -n $NAMESPACE
    
    echo ""
    echo "Ingress:"
    kubectl get ingress -n $NAMESPACE
    
    echo ""
    echo "HPA:"
    kubectl get hpa -n $NAMESPACE
}

show_urls() {
    log_info "Application URLs:"
    
    # Get ingress IP
    INGRESS_IP=$(kubectl get ingress fincompliance-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending")
    
    if [ "$INGRESS_IP" != "Pending" ] && [ "$INGRESS_IP" != "" ]; then
        echo "API: https://api.fincompliance.com (IP: $INGRESS_IP)"
        echo "UI: https://app.fincompliance.com (IP: $INGRESS_IP)"
    else
        echo "Ingress IP is pending. Check with: kubectl get ingress -n $NAMESPACE"
    fi
}

cleanup() {
    log_info "Cleaning up..."
    
    if [ "$ENVIRONMENT" = "prod" ]; then
        kubectl delete -k k8s/overlays/prod/
    else
        kubectl delete -k k8s/overlays/dev/
    fi
    
    log_success "Cleanup completed"
}

# Main function
main() {
    log_info "Starting FinCompliance RAG Portal deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Namespace: $NAMESPACE"
    log_info "Image Tag: $IMAGE_TAG"
    
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            authenticate_gcp
            build_and_push_image
            deploy_to_k8s
            wait_for_deployment
            show_status
            show_urls
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        "help")
            echo "Usage: $0 [deploy|status|cleanup|help]"
            echo ""
            echo "Commands:"
            echo "  deploy   - Deploy the application (default)"
            echo "  status   - Show deployment status"
            echo "  cleanup  - Remove the deployment"
            echo "  help     - Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  GCP_PROJECT_ID     - Google Cloud Project ID"
            echo "  GKE_CLUSTER_NAME   - GKE cluster name"
            echo "  GKE_ZONE           - GKE zone"
            echo "  GKE_REGION         - GKE region"
            echo "  K8S_NAMESPACE      - Kubernetes namespace"
            echo "  ENVIRONMENT        - Environment (dev/prod)"
            echo "  IMAGE_TAG          - Docker image tag"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
