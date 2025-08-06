#!/bin/bash

# Download UK Guidelines and Cochrane SoF data for OralHealth

echo "Creating data directories..."
mkdir -p data/uk_guidelines data/cochrane_sof

echo "Downloading UK Guidelines PDF..."
cd data/uk_guidelines
wget -q "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1030810/Delivering_better_oral_health.pdf"

echo "Downloading Cochrane SoF data..."
cd ../cochrane_sof

# Download sample Cochrane SoF CSV files
wget -q "https://raw.githubusercontent.com/your-username/CoE-Cochrane/main/validated/SoF/CD000979/CD000979.PUB3.csv" -O CD000979.csv 2>/dev/null || echo "Sample SoF file not available"

echo "Data download complete!"
echo "Run: python manage.py populate_uk_guidelines"
echo "Run: python manage.py import_cochrane_sof data/cochrane_sof"