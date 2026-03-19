#!/bin/bash
# Doctor Doom - Demo Data Generator
# Generates realistic thermal inspection data for testing

set -e

echo "========================================"
echo "Doctor Doom - Demo Data Generator"
echo "========================================"

# Configuration
SITE_COUNT=${1:-3}
MODULES_PER_SITE=${2:-20}
DEFECT_RATE=${3:-0.3}  # 30% of modules have defects

echo "Generating demo data:"
echo "  Sites: ${SITE_COUNT}"
echo "  Modules per site: ${MODULES_PER_SITE}"
echo "  Defect rate: ${DEFECT_RATE}"

# Generate thermal image simulation data
generate_thermal_data() {
    local module_id=$1
    local has_defect=$2
    
    echo "{"
    echo "  \"module_id\": \"${module_id}\","
    echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    
    if [ "$has_defect" = "true" ]; then
        local severity=("low" "medium" "high" "critical")
        local types=("hotspot" "cell_anomaly" "delamination" "diode_failure")
        local sev=${severity[$RANDOM % ${#severity[@]}]}
        local type=${types[$RANDOM % ${#types[@]}]}
        
        echo "  \"defect\": {"
        echo "    \"type\": \"${type}\","
        echo "    \"severity\": \"${sev}\","
        echo "    \"confidence\": $(echo "scale=2; 0.6 + ($RANDOM % 40) / 100" | bc),"
        echo "    \"temperature_delta\": $(echo "scale=1; 5 + ($RANDOM % 30)" | bc)"
        echo "  }"
    else
        echo "  \"defect\": null"
    fi
    
    echo "}"
}

# Create sample thermal image files
create_sample_images() {
    echo "Creating sample thermal image metadata..."
    
    for site in $(seq 1 $SITE_COUNT); do
        for module in $(seq 1 $MODULES_PER_SITE); do
            module_id="mod_$(printf '%03d' $site)_$(printf '%03d' $module)"
            
            # 30% chance of defect
            has_defect="false"
            if (( RANDOM % 100 < 30 )); then
                has_defect="true"
            fi
            
            generate_thermal_data "$module_id" "$has_defect" > "data/thermal_${module_id}.json"
        done
    done
    
    echo "✓ Generated $((SITE_COUNT * MODULES_PER_SITE)) thermal image metadata files"
}

# Generate flight plan
generate_flight_plan() {
    echo "Generating sample flight plan..."
    
    cat > data/sample_flight_plan.json << 'EOF'
{
  "name": "Demo Survey Mission",
  "site_id": "site_001",
  "altitude_m": 50,
  "speed_m_s": 5,
  "overlap_percent": 80,
  "sidelap_percent": 60,
  "waypoints": [
    {"lat": 13.7000, "lng": 100.5000, "action": "takeoff"},
    {"lat": 13.7010, "lng": 100.5000, "action": "capture"},
    {"lat": 13.7020, "lng": 100.5000, "action": "capture"},
    {"lat": 13.7020, "lng": 100.5010, "action": "capture"},
    {"lat": 13.7010, "lng": 100.5010, "action": "capture"},
    {"lat": 13.7000, "lng": 100.5010, "action": "capture"},
    {"lat": 13.7000, "lng": 100.5000, "action": "land"}
  ]
}
EOF
    
    echo "✓ Generated sample flight plan"
}

# Generate sample report configuration
generate_report_config() {
    echo "Generating sample report configuration..."
    
    cat > data/sample_report_config.json << 'EOF'
{
  "site_id": "site_001",
  "inspection_id": "insp_001",
  "report_type": "inspection",
  "format": "pdf",
  "include_thermal_images": true,
  "include_recommendations": true,
  "sections": [
    "executive_summary",
    "site_overview",
    "defect_summary",
    "detailed_findings",
    "thermal_images",
    "recommendations",
    "appendix"
  ],
  "branding": {
    "company_name": "Solar Inspect Co.",
    "logo_url": "/logo.png",
    "contact_email": "info@solarinspect.com"
  }
}
EOF
    
    echo "✓ Generated sample report configuration"
}

# Main execution
mkdir -p data

create_sample_images
generate_flight_plan
generate_report_config

echo ""
echo "========================================"
echo "Demo data generation complete!"
echo "========================================"
echo ""
echo "Generated files:"
echo "  - data/thermal_*.json (${SITE_COUNT} x ${MODULES_PER_SITE} files)"
echo "  - data/sample_flight_plan.json"
echo "  - data/sample_report_config.json"
echo ""
