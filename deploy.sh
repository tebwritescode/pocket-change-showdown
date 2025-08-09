#!/bin/bash

# PCS Tracker Kubernetes Deployment Script
# Usage: ./deploy.sh [namespace]

NAMESPACE=${1:-pcs-tracker}
VERSION="v2.0.0"

echo "🚀 Deploying PCS Tracker ${VERSION} to namespace: ${NAMESPACE}"
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

# Deploy using all-in-one file
echo ""
echo "📦 Applying Kubernetes resources..."
kubectl apply -f k8s/all-in-one.yaml

# Wait for deployment to be ready
echo ""
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/pcs-tracker -n ${NAMESPACE}

# Get service information
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Deployment Status:"
kubectl get deployment pcs-tracker -n ${NAMESPACE}

echo ""
echo "🔗 Service Information:"
kubectl get service -n ${NAMESPACE}

echo ""
echo "🌐 Access Information:"
echo "-------------------"

# Check if LoadBalancer is available
LB_IP=$(kubectl get service pcs-tracker-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
if [ ! -z "$LB_IP" ]; then
    echo "LoadBalancer IP: http://${LB_IP}"
fi

# Get NodePort
NODE_PORT=$(kubectl get service pcs-tracker-nodeport -n ${NAMESPACE} -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
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
echo "kubectl port-forward -n ${NAMESPACE} deployment/pcs-tracker 5001:5001"
echo "Then access at: http://localhost:5001"

echo ""
echo "📝 View logs:"
echo "kubectl logs -f deployment/pcs-tracker -n ${NAMESPACE}"

echo ""
echo "🎉 PCS Tracker ${VERSION} deployment complete!"