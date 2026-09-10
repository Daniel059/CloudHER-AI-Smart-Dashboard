#!/usr/bin/env bash
# package_lambdas.sh
#
# Zips each Lambda function and uploads it to the S3 bucket you pass as the
# LambdaDeploymentBucket parameter when deploying main-template.yaml.
#
# Usage:
#   ./scripts/package_lambdas.sh <your-deployment-bucket-name>
#
# Requires: AWS CLI configured with credentials that can write to the bucket.

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <deployment-bucket-name>"
    exit 1
fi

BUCKET_NAME="$1"
LAMBDA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../lambda" && pwd)"
BUILD_DIR="$(mktemp -d)"

echo "Building Lambda packages in: $BUILD_DIR"

package() {
    local handler_file="$1"
    local zip_name="$2"

    cp "$LAMBDA_DIR/$handler_file" "$BUILD_DIR/"
    (cd "$BUILD_DIR" && zip -q "$zip_name" "$handler_file")
    echo "Uploading $zip_name to s3://$BUCKET_NAME/$zip_name"
    aws s3 cp "$BUILD_DIR/$zip_name" "s3://$BUCKET_NAME/$zip_name"
}

package "analyzer_handler.py" "analyzer_function.zip"
package "contact_handler.py" "contact_function.zip"
package "dashboard_handler.py" "dashboard_function.zip"

rm -rf "$BUILD_DIR"

echo ""
echo "All three Lambda packages uploaded to s3://$BUCKET_NAME/"
echo "You can now deploy the stack with:"
echo ""
echo "  aws cloudformation deploy \\"
echo "    --template-file Infrastructure/main-template.yaml \\"
echo "    --stack-name cloudher-ai-smart-dashboard \\"
echo "    --capabilities CAPABILITY_NAMED_IAM \\"
echo "    --parameter-overrides \\"
echo "      LambdaDeploymentBucket=$BUCKET_NAME \\"
echo "      GroqApiKey=YOUR_GROQ_API_KEY \\"
echo "      SenderEmail=you@example.com \\"
echo "      RecipientEmail=you@example.com"