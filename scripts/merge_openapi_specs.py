#!/usr/bin/env python3
"""
OpenAPI Spec Merger for theraGENOME
=====================================
Merges OpenAPI YAML files from Dev 1, Dev 2, and Dev 3 into a unified specification.

Usage:
    python merge_openapi_specs.py

Output:
    - unified_api.yaml: Complete merged OpenAPI spec with all services
    - merge_report.json: Detailed merge report with validation info
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging

# ============================================================================
# Configuration
# ============================================================================

SPECS_DIR = Path(__file__).parent.parent / "openapi_specs"
OUTPUT_DIR = Path(__file__).parent.parent / "api_gateway"
SPEC_FILES = {
    "dev1": "variant_api.openapi.yaml",
    "dev1_alt": "classification_api.openapi.yaml",
    "dev2": "pathogen_resistance_api.openapi.yaml",
    "dev3": "drug_safety_api.openapi.yaml",
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUT_DIR / "merge.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# OpenAPI Merger Class
# ============================================================================

class OpenAPIMerger:
    """Merges multiple OpenAPI specifications into a unified spec."""
    
    def __init__(self):
        """Initialize the merger."""
        self.specs: Dict[str, Dict] = {}
        self.merged_spec: Dict[str, Any] = {}
        self.merge_report: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "specs_loaded": [],
            "errors": [],
            "warnings": [],
            "merge_result": {}
        }
    
    def load_specs(self) -> bool:
        """Load all OpenAPI YAML specifications."""
        logger.info(f"Loading OpenAPI specs from {SPECS_DIR}")
        
        for dev_key, filename in SPEC_FILES.items():
            spec_path = SPECS_DIR / filename
            
            if not spec_path.exists():
                warning = f"Spec not found: {spec_path}"
                logger.warning(warning)
                self.merge_report["warnings"].append(warning)
                continue
            
            try:
                with open(spec_path, 'r', encoding='utf-8') as f:
                    spec = yaml.safe_load(f)
                self.specs[dev_key] = spec
                self.merge_report["specs_loaded"].append({
                    "name": dev_key,
                    "file": filename,
                    "title": spec.get("info", {}).get("title"),
                    "version": spec.get("info", {}).get("version")
                })
                logger.info(f"✓ Loaded {dev_key}: {spec.get('info', {}).get('title')}")
            except Exception as e:
                error = f"Error loading {spec_path}: {str(e)}"
                logger.error(error)
                self.merge_report["errors"].append(error)
                return False
        
        if not self.specs:
            error = "No specs loaded successfully"
            logger.error(error)
            self.merge_report["errors"].append(error)
            return False
        
        logger.info(f"✓ Loaded {len(self.specs)} specifications")
        return True
    
    def merge(self) -> bool:
        """Merge all loaded specs into unified specification."""
        logger.info("Merging OpenAPI specifications...")
        
        try:
            # Initialize merged spec with base from first spec
            base_spec = next(iter(self.specs.values()))
            
            self.merged_spec = {
                "openapi": base_spec.get("openapi", "3.0.0"),
                "info": {
                    "title": "theraGENOME Unified API",
                    "description": "Unified OpenAPI specification for theraGENOME microservices",
                    "version": "1.0.0",
                    "contact": {
                        "name": "theraGENOME Development Team",
                        "email": "dev@theragenome.com"
                    },
                    "license": {
                        "name": "MIT",
                        "url": "https://opensource.org/licenses/MIT"
                    },
                    "x-api-id": "theragenome-unified-api",
                    "x-api-lifetime": "production"
                },
                "servers": self._merge_servers(),
                "paths": {},
                "components": {
                    "schemas": {},
                    "securitySchemes": {},
                    "responses": {},
                    "parameters": {},
                    "examples": {},
                    "requestBodies": {},
                    "headers": {}
                },
                "security": [],
                "tags": [],
                "x-merged-specs": list(self.specs.keys()),
                "x-merge-date": datetime.now().isoformat()
            }
            
            # Merge paths
            self._merge_paths()
            
            # Merge components
            self._merge_components()
            
            # Merge security schemes
            self._merge_security_schemes()
            
            # Generate tags
            self._generate_tags()
            
            logger.info("✓ Merge completed successfully")
            return True
            
        except Exception as e:
            error = f"Merge failed: {str(e)}"
            logger.error(error)
            self.merge_report["errors"].append(error)
            return False
    
    def _merge_servers(self) -> List[Dict]:
        """Merge server configurations."""
        servers = []
        for spec_key, spec in self.specs.items():
            if "servers" in spec:
                for server in spec["servers"]:
                    # Deduplicate servers
                    if server not in servers:
                        servers.append(server)
        
        # Ensure at least one server
        if not servers:
            servers = [
                {"url": "https://api.theragenome.com", "description": "Production"}
            ]
        
        return servers
    
    def _merge_paths(self) -> None:
        """Merge all paths from all specs."""
        logger.info("Merging paths...")
        path_count = 0
        
        for spec_key, spec in self.specs.items():
            if "paths" not in spec:
                continue
            
            for path, path_item in spec["paths"].items():
                if path not in self.merged_spec["paths"]:
                    self.merged_spec["paths"][path] = {}
                
                # Merge methods in path
                for method, operation in path_item.items():
                    if method.startswith("x-"):  # Skip extensions
                        continue
                    
                    if method in self.merged_spec["paths"][path]:
                        logger.warning(f"Duplicate method {method} in path {path}, keeping first")
                        continue
                    
                    # Add operation tags
                    if "tags" not in operation:
                        operation["tags"] = [spec_key]
                    
                    self.merged_spec["paths"][path][method] = operation
                    path_count += 1
        
        logger.info(f"✓ Merged {path_count} API operations")
    
    def _merge_components(self) -> None:
        """Merge component schemas and definitions."""
        logger.info("Merging components...")
        
        for spec_key, spec in self.specs.items():
            if "components" not in spec:
                continue
            
            components = spec["components"]
            
            # Merge schemas
            if "schemas" in components:
                for schema_name, schema_def in components["schemas"].items():
                    if schema_name in self.merged_spec["components"]["schemas"]:
                        logger.warning(f"Duplicate schema {schema_name}, keeping first")
                        continue
                    self.merged_spec["components"]["schemas"][schema_name] = schema_def
            
            # Merge security schemes
            if "securitySchemes" in components:
                for scheme_name, scheme_def in components["securitySchemes"].items():
                    if scheme_name not in self.merged_spec["components"]["securitySchemes"]:
                        self.merged_spec["components"]["securitySchemes"][scheme_name] = scheme_def
            
            # Merge responses
            if "responses" in components:
                for response_name, response_def in components["responses"].items():
                    if response_name not in self.merged_spec["components"]["responses"]:
                        self.merged_spec["components"]["responses"][response_name] = response_def
            
            # Merge parameters
            if "parameters" in components:
                for param_name, param_def in components["parameters"].items():
                    if param_name not in self.merged_spec["components"]["parameters"]:
                        self.merged_spec["components"]["parameters"][param_name] = param_def
        
        logger.info(f"✓ Merged schemas: {len(self.merged_spec['components']['schemas'])}")
    
    def _merge_security_schemes(self) -> None:
        """Merge security schemes and set default security."""
        for spec_key, spec in self.specs.items():
            if "security" in spec and isinstance(spec["security"], list):
                for security_item in spec["security"]:
                    if security_item not in self.merged_spec["security"]:
                        self.merged_spec["security"].append(security_item)
        
        # Set default security
        if not self.merged_spec["security"]:
            self.merged_spec["security"] = [{"bearerAuth": []}]
    
    def _generate_tags(self) -> None:
        """Generate tag documentation from merged specs."""
        tags_dict = {}
        
        for spec_key, spec in self.specs.items():
            if "tags" in spec:
                for tag in spec["tags"]:
                    if tag["name"] not in tags_dict:
                        tags_dict[tag["name"]] = tag
        
        # Add service tags
        service_tags = [
            {"name": "dev1", "description": "Dev 1: Variant Classification"},
            {"name": "dev2", "description": "Dev 2: Pathogen Resistance"},
            {"name": "dev3", "description": "Dev 3: Drug Safety & Toxicity"}
        ]
        
        for tag in service_tags:
            if tag["name"] not in tags_dict:
                tags_dict[tag["name"]] = tag
        
        self.merged_spec["tags"] = list(tags_dict.values())
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate merged specification."""
        logger.info("Validating merged specification...")
        issues = []
        
        # Check required fields
        if not self.merged_spec.get("openapi"):
            issues.append("Missing OpenAPI version")
        
        if not self.merged_spec.get("info"):
            issues.append("Missing info object")
        
        if not self.merged_spec.get("paths"):
            issues.append("No paths defined in merged spec")
        
        # Check path definitions
        for path, methods in self.merged_spec.get("paths", {}).items():
            if not methods:
                issues.append(f"Empty methods for path {path}")
        
        if issues:
            logger.warning(f"Validation found {len(issues)} issues")
            for issue in issues:
                logger.warning(f"  - {issue}")
                self.merge_report["warnings"].append(issue)
        else:
            logger.info("✓ Validation passed")
        
        return len(issues) == 0, issues
    
    def save(self, output_file: Path = None) -> bool:
        """Save merged specification to YAML file."""
        if output_file is None:
            output_file = OUTPUT_DIR / "unified_api.yaml"
        
        try:
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save as YAML
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.merged_spec, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"✓ Saved unified spec to {output_file}")
            
            # Also save as JSON
            json_file = output_file.with_suffix('.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.merged_spec, f, indent=2)
            
            logger.info(f"✓ Saved unified spec (JSON) to {json_file}")
            return True
            
        except Exception as e:
            error = f"Failed to save specification: {str(e)}"
            logger.error(error)
            self.merge_report["errors"].append(error)
            return False
    
    def generate_report(self, report_file: Path = None) -> bool:
        """Generate merge report."""
        if report_file is None:
            report_file = OUTPUT_DIR / "merge_report.json"
        
        try:
            # Update report with results
            self.merge_report["status"] = "success" if not self.merge_report["errors"] else "failed"
            self.merge_report["merge_result"] = {
                "paths_count": len(self.merged_spec.get("paths", {})),
                "schemas_count": len(self.merged_spec.get("components", {}).get("schemas", {})),
                "security_schemes_count": len(self.merged_spec.get("components", {}).get("securitySchemes", {})),
                "tags_count": len(self.merged_spec.get("tags", []))
            }
            
            # Save report
            report_file.parent.mkdir(parents=True, exist_ok=True)
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.merge_report, f, indent=2)
            
            logger.info(f"✓ Saved merge report to {report_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")
            return False
    
    def print_summary(self) -> None:
        """Print merge summary."""
        print("\n" + "="*70)
        print("OpenAPI Merge Summary")
        print("="*70)
        
        print(f"\n✓ Specifications Merged: {len(self.specs_loaded)}")
        for spec in self.merge_report["specs_loaded"]:
            print(f"  - {spec['name']}: {spec['title']} v{spec['version']}")
        
        print(f"\n📊 Merged Result:")
        print(f"  - Paths: {self.merge_report['merge_result'].get('paths_count', 0)}")
        print(f"  - Schemas: {self.merge_report['merge_result'].get('schemas_count', 0)}")
        print(f"  - Security Schemes: {self.merge_report['merge_result'].get('security_schemes_count', 0)}")
        print(f"  - Tags: {self.merge_report['merge_result'].get('tags_count', 0)}")
        
        if self.merge_report["warnings"]:
            print(f"\n⚠️  Warnings ({len(self.merge_report['warnings'])}):")
            for warning in self.merge_report["warnings"][:5]:
                print(f"  - {warning}")
        
        if self.merge_report["errors"]:
            print(f"\n❌ Errors ({len(self.merge_report['errors'])}):")
            for error in self.merge_report["errors"]:
                print(f"  - {error}")
        else:
            print(f"\n✅ Status: {self.merge_report['status'].upper()}")
        
        print("\n" + "="*70 + "\n")

# ============================================================================
# Main Function
# ============================================================================

def main() -> int:
    """Main entry point."""
    logger.info("="*70)
    logger.info("theraGENOME OpenAPI Spec Merger")
    logger.info("="*70)
    
    # Create merger instance
    merger = OpenAPIMerger()
    
    # Load specs
    if not merger.load_specs():
        logger.error("Failed to load specifications")
        return 1
    
    # Merge specs
    if not merger.merge():
        logger.error("Failed to merge specifications")
        return 1
    
    # Validate
    is_valid, _ = merger.validate()
    if not is_valid:
        logger.warning("Validation found issues but continuing...")
    
    # Save output
    if not merger.save():
        logger.error("Failed to save merged specification")
        return 1
    
    # Generate report
    if not merger.generate_report():
        logger.error("Failed to generate report")
        return 1
    
    # Print summary
    merger.print_summary()
    
    logger.info("✅ Merge completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
