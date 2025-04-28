#!/bin/bash

# Create a clean build directory
echo "Cleaning up previous builds..."
rm -rf build
mkdir -p build

# Install production dependencies
echo "Installing production dependencies..."
npm install --production

# Copy source files
echo "Copying source files..."
cp -r src package.json build/

# Install dependencies in the build directory
echo "Installing dependencies in the build directory..."
cd build
npm install --production
cd ..

# Create Lambda ZIP
echo "Creating Lambda deployment package..."
cd build
zip -r ../lambda.zip .
cd ..

echo "Lambda deployment package created: lambda.zip"
echo "You can now deploy this package using Terraform." 