#!/bin/bash
# TheraGenome Container Security Scanning Script
# Scans Docker images for vulnerabilities before deployment

set -e

# Configuration
REGISTRY="${REGISTRY:-docker.io}"
NAMESPACE="${NAMESPACE:-theragenome}"
TRIVY_SEVERITY="${TRIVY_SEVERITY:-MEDIUM,HIGH,CRITICAL}"
FAIL_ON_SEVERITY="${FAIL_ON_SEVERITY:-CRITICAL}"
SCAN_RESULTS_DIR="./scan_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check prerequisites
check_prerequisites() {
  log_info "Checking prerequisites..."
  
  if ! command -v docker &> /dev/null; then
    log_error "Docker not found. Please install Docker."
    exit 1
  fi
  
  if ! command -v trivy &> /dev/null; then
    log_warning "Trivy not found. Installing Trivy..."
    
    # Install Trivy
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
      curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
    elif [[ "$OSTYPE" == "darwin"* ]]; then
      brew install aquasecurity/trivy/trivy
    fi
  fi
  
  if ! command -v syft &> /dev/null; then
    log_warning "Syft not found. Installing Syft..."
    curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
  fi
  
  log_success "Prerequisites check passed"
}

# Scan Dockerfile for security best practices
scan_dockerfile() {
  local dockerfile="$1"
  
  log_info "Scanning Dockerfile: $dockerfile"
  
  local issues=0
  local warnings=0
  
  # Check for security issues
  if grep -q "^FROM.*:latest" "$dockerfile"; then
    log_warning "Dockerfile uses 'latest' tag (may cause inconsistencies)"
    ((warnings++))
  fi
  
  if ! grep -q "^USER" "$dockerfile"; then
    log_error "Dockerfile missing USER instruction (should run as non-root)"
    ((issues++))
  fi
  
  if ! grep -q "^RUN.*apt-get.*--no-install-recommends" "$dockerfile" && grep -q "apt-get" "$dockerfile"; then
    log_warning "Dockerfile apt-get should use --no-install-recommends"
    ((warnings++))
  fi
  
  if grep -q "^RUN.*sudo" "$dockerfile"; then
    log_error "Dockerfile uses sudo (unnecessary in containers)"
    ((issues++))
  fi
  
  if ! grep -q "^HEALTHCHECK" "$dockerfile" && grep -q "CMD.*server\|EXPOSE" "$dockerfile"; then
    log_warning "Dockerfile missing HEALTHCHECK instruction"
    ((warnings++))
  fi
  
  if grep -q "COPY.*\." "$dockerfile" && ! grep -q "\.dockerignore" "$(dirname "$dockerfile")/.dockerignore" 2>/dev/null; then
    log_warning "Project may be missing .dockerignore file"
    ((warnings++))
  fi
  
  echo "  Issues: $issues, Warnings: $warnings"
  return $issues
}

# Scan Docker image for vulnerabilities
scan_image() {
  local image="$1"
  local severity="$2"
  
  log_info "Scanning Docker image: $image"
  
  # Create results directory
  mkdir -p "$SCAN_RESULTS_DIR"
  
  # Scan with Trivy
  local report_file="$SCAN_RESULTS_DIR/${image//\//_}_${TIMESTAMP}.json"
  local html_report="$SCAN_RESULTS_DIR/${image//\//_}_${TIMESTAMP}.html"
  
  trivy image \
    --severity "$severity" \
    --format json \
    --output "$report_file" \
    "$image"
  
  trivy image \
    --severity "$severity" \
    --format template \
    --template '@/contrib/html.tpl' \
    --output "$html_report" \
    "$image"
  
  # Generate SBOM (Software Bill of Materials)
  local sbom_file="$SCAN_RESULTS_DIR/${image//\//_}_sbom_${TIMESTAMP}.json"
  syft "$image" -o cyclonedx-json > "$sbom_file"
  
  # Parse results
  local critical_count=$(jq '[.Results[]? | select(.Vulnerabilities[]? | select(.Severity=="CRITICAL"))] | length' "$report_file")
  local high_count=$(jq '[.Results[]? | select(.Vulnerabilities[]? | select(.Severity=="HIGH"))] | length' "$report_file")
  local medium_count=$(jq '[.Results[]? | select(.Vulnerabilities[]? | select(.Severity=="MEDIUM"))] | length' "$report_file")
  
  log_info "Scan Results for $image:"
  echo "  Critical: $critical_count"
  echo "  High: $high_count"
  echo "  Medium: $medium_count"
  echo "  Report: $report_file"
  echo "  HTML Report: $html_report"
  echo "  SBOM: $sbom_file"
  
  # Check if we should fail
  if [[ "$FAIL_ON_SEVERITY" == "CRITICAL" ]] && [[ $critical_count -gt 0 ]]; then
    log_error "Found CRITICAL vulnerabilities"
    return 1
  fi
  
  if [[ "$FAIL_ON_SEVERITY" == "HIGH" ]] && [[ $((high_count + critical_count)) -gt 0 ]]; then
    log_error "Found HIGH or CRITICAL vulnerabilities"
    return 1
  fi
  
  return 0
}

# Scan all images
scan_all_images() {
  log_info "Building and scanning all container images..."
  
  local build_failed=0
  
  # Build and scan API image
  log_info "Building theragenome-api image..."
  if docker build -t "$NAMESPACE/api:latest" -f Dockerfile .; then
    log_success "Built theragenome-api"
    scan_image "$NAMESPACE/api:latest" "$TRIVY_SEVERITY" || ((build_failed++))
  else
    log_error "Failed to build theragenome-api"
    ((build_failed++))
  fi
  
  # Build and scan TypeScript image
  log_info "Building variant-api image..."
  if docker build -t "$NAMESPACE/variant-api:latest" -f Dockerfile.deno .; then
    log_success "Built variant-api"
    scan_image "$NAMESPACE/variant-api:latest" "$TRIVY_SEVERITY" || ((build_failed++))
  else
    log_error "Failed to build variant-api"
    ((build_failed++))
  fi
  
  return $build_failed
}

# Generate security report
generate_report() {
  log_info "Generating security report..."
  
  local report_file="$SCAN_RESULTS_DIR/security_report_${TIMESTAMP}.md"
  
  cat > "$report_file" << 'EOF'
# TheraGenome Container Security Scan Report

**Scan Date:** $(date)
**Environment:** Production
**Scanner:** Trivy + Syft

## Executive Summary

### Scan Results

EOF

  # Add scan results
  for result in "$SCAN_RESULTS_DIR"/*_${TIMESTAMP}.json; do
    if [[ -f "$result" ]]; then
      local image_name=$(basename "$result" "_${TIMESTAMP}.json")
      local critical=$(jq '[.Results[]? | select(.Vulnerabilities[]? | select(.Severity=="CRITICAL"))] | length' "$result")
      local high=$(jq '[.Results[]? | select(.Vulnerabilities[]? | select(.Severity=="HIGH"))] | length' "$result")
      local medium=$(jq '[.Results[]? | select(.Vulnerabilities[]? | select(.Severity=="MEDIUM"))] | length' "$result")
      
      cat >> "$report_file" << EOF

| Image | Critical | High | Medium |
|-------|----------|------|--------|
| $image_name | $critical | $high | $medium |

EOF
    fi
  done
  
  cat >> "$report_file" << 'EOF'

## Remediation Steps

### Critical Vulnerabilities
- [ ] Fix all critical CVEs within 48 hours
- [ ] Update base image to patched version
- [ ] Rebuild and re-test containers

### High Vulnerabilities
- [ ] Fix all high CVEs within 1 week
- [ ] Test thoroughly before deployment
- [ ] Document justification if not fixed

### Medium Vulnerabilities
- [ ] Fix within 2 weeks
- [ ] Track in issue tracker
- [ ] Plan for future releases

## Recommendations

1. Set up automated vulnerability scanning in CI/CD
2. Implement image signing and verification
3. Use minimal base images (alpine, distroless)
4. Regular dependency updates
5. Use private registry with access controls

EOF

  log_success "Report generated: $report_file"
}

# Main execution
main() {
  log_info "Starting TheraGenome Container Security Scan"
  
  check_prerequisites
  
  # Scan Dockerfiles
  log_info "Scanning Dockerfiles..."
  scan_dockerfile "Dockerfile" || true
  scan_dockerfile "Dockerfile.deno" || true
  
  # Scan images
  scan_all_images || {
    log_error "Container scan failed with vulnerabilities"
    generate_report
    exit 1
  }
  
  # Generate final report
  generate_report
  
  log_success "Container security scan completed successfully"
  exit 0
}

main "$@"
