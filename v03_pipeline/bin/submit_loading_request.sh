#!/usr/bin/env bash

set -euo pipefail

# Default values
API_HOST="${API_HOST:-localhost}"
API_PORT="${API_PORT:-6000}"
CALLSET_PATH=""
PROJECT_GUIDS=""
SAMPLE_TYPE="WGS"
REFERENCE_GENOME="GRCh38"
DATASET_TYPE="SNV_INDEL"
SKIP_CHECK_SEX_AND_RELATEDNESS="false"
SKIP_EXPECT_TDR_METRICS="false"
VALIDATIONS_TO_SKIP="[]"

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Submit a loading pipeline request to the seqr loading API.

Required Options:
  --callset-path PATH           Path to VCF or Hail Matrix Table (required)
  --project-guids GUIDS         Comma-separated list of project GUIDs (required)

Optional Options:
  --sample-type TYPE            Sample type: WGS or WES (default: WGS)
  --reference-genome GENOME     Reference genome: GRCh37 or GRCh38 (default: GRCh38)
  --dataset-type TYPE           Dataset type: SNV_INDEL, MITO, SV, or GCNV (default: SNV_INDEL)
  --skip-check-sex              Skip sex and relatedness checks (default: false)
  --skip-expect-tdr-metrics     Skip TDR metrics expectation (default: false)
  --validations-to-skip LIST    JSON array of validations to skip (default: [])
  --api-host HOST               API host (default: localhost)
  --api-port PORT               API port (default: 6000)
  -h, --help                    Show this help message

Examples:
  # Basic SNV/INDEL load
  $0 --callset-path gs://bucket/sample.vcf.gz --project-guids R0001_project

  # Multiple projects
  $0 --callset-path /data/sample.vcf.gz --project-guids R0001_project,R0002_project

  # Mitochondrial data
  $0 --callset-path gs://bucket/mito.vcf.gz \\
     --project-guids R0001_project \\
     --dataset-type MITO \\
     --reference-genome GRCh38

  # Skip all validations
  $0 --callset-path /data/sample.vcf.gz \\
     --project-guids R0001_project \\
     --validations-to-skip '["all"]'

EOF
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --callset-path)
            CALLSET_PATH="$2"
            shift 2
            ;;
        --project-guids)
            PROJECT_GUIDS="$2"
            shift 2
            ;;
        --sample-type)
            SAMPLE_TYPE="$2"
            shift 2
            ;;
        --reference-genome)
            REFERENCE_GENOME="$2"
            shift 2
            ;;
        --dataset-type)
            DATASET_TYPE="$2"
            shift 2
            ;;
        --skip-check-sex)
            SKIP_CHECK_SEX_AND_RELATEDNESS="true"
            shift
            ;;
        --skip-expect-tdr-metrics)
            SKIP_EXPECT_TDR_METRICS="true"
            shift
            ;;
        --validations-to-skip)
            VALIDATIONS_TO_SKIP="$2"
            shift 2
            ;;
        --api-host)
            API_HOST="$2"
            shift 2
            ;;
        --api-port)
            API_PORT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Error: Unknown option $1"
            usage
            ;;
    esac
done

# Validate required arguments
if [[ -z "$CALLSET_PATH" ]]; then
    echo "Error: --callset-path is required"
    usage
fi

if [[ -z "$PROJECT_GUIDS" ]]; then
    echo "Error: --project-guids is required"
    usage
fi

# Convert comma-separated project GUIDs to JSON array
IFS=',' read -ra GUID_ARRAY <<< "$PROJECT_GUIDS"
PROJECT_GUIDS_JSON="["
for i in "${!GUID_ARRAY[@]}"; do
    if [[ $i -gt 0 ]]; then
        PROJECT_GUIDS_JSON+=","
    fi
    PROJECT_GUIDS_JSON+="\"${GUID_ARRAY[$i]}\""
done
PROJECT_GUIDS_JSON+="]"

# Build JSON payload
JSON_PAYLOAD=$(cat <<EOF
{
  "request_type": "LoadingPipelineRequest",
  "callset_path": "$CALLSET_PATH",
  "project_guids": $PROJECT_GUIDS_JSON,
  "sample_type": "$SAMPLE_TYPE",
  "reference_genome": "$REFERENCE_GENOME",
  "dataset_type": "$DATASET_TYPE",
  "skip_check_sex_and_relatedness": $SKIP_CHECK_SEX_AND_RELATEDNESS,
  "skip_expect_tdr_metrics": $SKIP_EXPECT_TDR_METRICS,
  "validations_to_skip": $VALIDATIONS_TO_SKIP
}
EOF
)

# Submit request
API_URL="http://${API_HOST}:${API_PORT}/loading_pipeline_enqueue"

echo "Submitting loading pipeline request to $API_URL"
echo "Payload:"
echo "$JSON_PAYLOAD" | jq '.' 2>/dev/null || echo "$JSON_PAYLOAD"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD" \
    "$API_URL")

HTTP_BODY=$(echo "$RESPONSE" | sed -e 's/HTTP_STATUS\:.*//g')
HTTP_STATUS=$(echo "$RESPONSE" | tr -d '\n' | sed -e 's/.*HTTP_STATUS://')

echo "Response (HTTP $HTTP_STATUS):"
echo "$HTTP_BODY" | jq '.' 2>/dev/null || echo "$HTTP_BODY"

if [[ "$HTTP_STATUS" -eq 202 ]]; then
    echo ""
    echo "✓ Request successfully queued"
    exit 0
else
    echo ""
    echo "✗ Request failed with status $HTTP_STATUS"
    exit 1
fi
