# Optimize GitHub Runners and Improve PR Messages

This PR makes the following improvements to Inframate:

## 1. Optimized GitHub Runner Packages

- **Modular Dependency Structure**: Reorganized dependencies in `setup.py` into core, RAG, web, and dev groups
- **Minimal Installation in CI/CD**: Modified GitHub workflow to install only necessary packages for analysis
- **Documentation**: Added installation instructions for different dependency combinations

### Before & After Comparison

**Before:**
- All packages installed at once (approximately 20+ packages with large dependencies)
- Heavy packages like sentence-transformers and faiss-cpu always installed

**After:**
- Core dependencies only: ~10 essential packages
- Optional components installed only when needed
- CI/CD pipeline uses minimal set of dependencies

## 2. Enhanced PR Messages

- **Infrastructure Structure**: Automatically detects and includes the infrastructure components  
- **Cost Estimation**: Extracts and includes cost estimates in the PR message
- **Better Documentation**: Improved readability of deployment instructions

## 3. Benefits

- **Faster Builds**: Reduced CI/CD pipeline execution time
- **Lower Resource Usage**: Minimized memory and CPU usage in GitHub Runners
- **Improved Decision-Making**: Cost estimates and infrastructure diagrams help with approval decisions
- **Better Documentation**: Clear explanations of infrastructure components 