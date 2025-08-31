#!/bin/bash

# PCS Tracker Kubernetes Deployment Script
# Usage: ./deploy.sh [variant]
# variant: 'standard' (default) or 'mom'

# Show help if requested
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "PCS Tracker Kubernetes Deployment Script"
    echo ""
    echo "Usage: ./deploy.sh [variant]"
    echo ""
    echo "Variants:"
    echo "  standard    Deploy to 'pocket-change-showdown' namespace (default)"
    echo "  mom         Deploy to 'pocket-change-showdown-mom' namespace"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh          # Deploy standard variant"
    echo "  ./deploy.sh standard # Deploy standard variant"
    echo "  ./deploy.sh mom      # Deploy mom variant"
    echo ""
    exit 0
fi

VARIANT=${1:-standard}
VERSION="v2.1.1"

# Validate variant
if [ "$VARIANT" != "standard" ] && [ "$VARIANT" != "mom" ]; then
    echo "❌ Invalid variant: ${VARIANT}"
    echo "Valid variants: standard, mom"
    echo "Use './deploy.sh --help' for usage information"
    exit 1
fi

# Set configuration based on variant
if [ "$VARIANT" = "mom" ]; then
    NAMESPACE="pocket-change-showdown-mom"
    MANIFEST_FILE="k8s/all-in-one-mom.yaml"
    DEPLOYMENT_NAME="pocket-change-showdown-mom"
    SERVICE_NAME="pocket-change-showdown-mom-service"
    NODEPORT_NAME="pocket-change-showdown-mom-nodeport"
else
    NAMESPACE="pocket-change-showdown"
    MANIFEST_FILE="k8s/all-in-one.yaml"
    DEPLOYMENT_NAME="pocket-change-showdown"
    SERVICE_NAME="pocket-change-showdown-service"
    NODEPORT_NAME="pocket-change-showdown-nodeport"
fi

# Validate manifest file exists
if [ ! -f "$MANIFEST_FILE" ]; then
    echo "❌ Manifest file not found: ${MANIFEST_FILE}"
    exit 1
fi

echo "🚀 Deploying PCS Tracker ${VERSION} (${VARIANT}) to namespace: ${NAMESPACE}"
echo "================================================"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Not connected to a Kubernetes cluster. Please configure kubectl."
    exit 1
fi

echo "✅ kubectl configured and connected to cluster"

# Deploy using appropriate manifest file
echo ""
echo "📦 Applying Kubernetes resources from ${MANIFEST_FILE}..."
kubectl apply -f ${MANIFEST_FILE}

# Wait for deployment to be ready
echo ""
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE}

# Get service information
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Deployment Status:"
kubectl get deployment ${DEPLOYMENT_NAME} -n ${NAMESPACE}

echo ""
echo "🔗 Service Information:"
kubectl get service -n ${NAMESPACE}

echo ""
echo "🌐 Access Information:"
echo "-------------------"

# Check if LoadBalancer is available
LB_IP=$(kubectl get service ${SERVICE_NAME} -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
if [ ! -z "$LB_IP" ]; then
    echo "LoadBalancer IP: http://${LB_IP}"
fi

# Get NodePort
NODE_PORT=$(kubectl get service ${NODEPORT_NAME} -n ${NAMESPACE} -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
if [ ! -z "$NODE_PORT" ]; then
    echo "NodePort: Access via http://<node-ip>:${NODE_PORT}"
    
    # Try to get node IP (works on some clusters)
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}' 2>/dev/null)
    if [ -z "$NODE_IP" ]; then
        NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null)
    fi
    
    if [ ! -z "$NODE_IP" ]; then
        echo "  Example: http://${NODE_IP}:${NODE_PORT}"
    fi
fi

# Port forwarding instructions
echo ""
echo "📡 For local access via port forwarding:"
echo "kubectl port-forward -n ${NAMESPACE} deployment/${DEPLOYMENT_NAME} 5001:5001"
echo "Then access at: http://localhost:5001"

echo ""
echo "📝 View logs:"
echo "kubectl logs -f deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE}"

echo ""
echo "🎉 PCS Tracker ${VERSION} deployment complete!"