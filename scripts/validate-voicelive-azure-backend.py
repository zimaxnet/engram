#!/usr/bin/env python3
"""
Validate VoiceLive Configuration in Azure Backend

This script validates the VoiceLive configuration in the deployed Azure backend:
- Environment variables
- Endpoint connectivity
- Configuration correctness
- WebSocket proxy readiness
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional

import httpx

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text: str):
    print(f"ℹ️  {text}")

async def get_azure_container_app_env(
    app_name: str,
    resource_group: str,
    env_var_name: str
) -> tuple[Optional[str], Optional[str]]:
    """Get environment variable from Azure Container App.
    
    Returns:
        (value, secret_ref): The value and secret reference if it's a secret
    """
    try:
        import subprocess
        import json
        
        # Get both value and secretRef
        cmd = [
            "az", "containerapp", "show",
            "--name", app_name,
            "--resource-group", resource_group,
            "--query", f"properties.template.containers[0].env[?name=='{env_var_name}']",
            "-o", "json"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        env_data = json.loads(result.stdout.strip())
        
        if env_data and len(env_data) > 0:
            env_item = env_data[0]
            value = env_item.get("value")
            secret_ref = env_item.get("secretRef")
            return (value, secret_ref)
        return (None, None)
    except subprocess.CalledProcessError:
        return (None, None)
    except FileNotFoundError:
        print_error("Azure CLI not found. Install it to check environment variables.")
        return (None, None)
    except json.JSONDecodeError:
        return (None, None)

async def validate_environment_variables(
    app_name: str,
    resource_group: str
) -> dict:
    """Validate required environment variables."""
    print_header("Validating Environment Variables")
    
    required_vars = {
        "AZURE_VOICELIVE_ENDPOINT": "VoiceLive endpoint URL",
        "AZURE_VOICELIVE_KEY": "VoiceLive API key (secret)",
        "AZURE_VOICELIVE_MODEL": "VoiceLive model name",
        "AZURE_VOICELIVE_API_VERSION": "VoiceLive API version",
    }
    
    optional_vars = {
        "AZURE_VOICELIVE_PROJECT_NAME": "VoiceLive project name (for unified endpoints)",
        "AZURE_VOICELIVE_AGENT_ID": "Default agent ID",
    }
    
    results = {
        "required": {},
        "optional": {},
        "missing_required": [],
        "all_present": True
    }
    
    # Check required variables
    for var_name, description in required_vars.items():
        value, secret_ref = await get_azure_container_app_env(app_name, resource_group, var_name)
        if value:
            # Mask sensitive values
            display_value = value
            if "KEY" in var_name or "SECRET" in var_name:
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            results["required"][var_name] = value
            print_success(f"{var_name}: {display_value}")
        elif secret_ref:
            # Variable is stored as a secret reference
            results["required"][var_name] = f"[Secret: {secret_ref}]"
            print_success(f"{var_name}: [Secret Reference: {secret_ref}]")
        else:
            results["missing_required"].append(var_name)
            results["all_present"] = False
            print_error(f"{var_name}: NOT SET - {description}")
    
    # Check optional variables
    for var_name, description in optional_vars.items():
        value, secret_ref = await get_azure_container_app_env(app_name, resource_group, var_name)
        if value:
            results["optional"][var_name] = value
            print_success(f"{var_name}: {value}")
        elif secret_ref:
            results["optional"][var_name] = f"[Secret: {secret_ref}]"
            print_success(f"{var_name}: [Secret Reference: {secret_ref}]")
        else:
            print_warning(f"{var_name}: NOT SET (optional) - {description}")
    
    return results

async def test_backend_health(backend_url: str) -> bool:
    """Test backend health endpoint."""
    print_header("Testing Backend Health")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{backend_url}/health")
            if response.status_code == 200:
                print_success(f"Backend health check passed: {response.status_code}")
                try:
                    data = response.json()
                    print_info(f"Response: {json.dumps(data, indent=2)}")
                except:
                    print_info(f"Response: {response.text[:200]}")
                return True
            else:
                print_error(f"Backend health check failed: {response.status_code}")
                print_info(f"Response: {response.text[:200]}")
                return False
    except httpx.TimeoutException:
        print_error("Backend health check timed out")
        return False
    except Exception as e:
        print_error(f"Backend health check error: {e}")
        return False

async def test_voicelive_config_endpoint(backend_url: str) -> bool:
    """Test VoiceLive configuration endpoint."""
    print_header("Testing VoiceLive Configuration Endpoint")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test the config endpoint (if it exists)
            response = await client.get(f"{backend_url}/api/v1/voice/config")
            if response.status_code == 200:
                print_success(f"VoiceLive config endpoint accessible: {response.status_code}")
                try:
                    data = response.json()
                    print_info(f"Config: {json.dumps(data, indent=2)}")
                except:
                    print_info(f"Response: {response.text[:200]}")
                return True
            elif response.status_code == 404:
                print_warning("VoiceLive config endpoint not found (may not be implemented)")
                return True  # Not a critical failure
            else:
                print_error(f"VoiceLive config endpoint error: {response.status_code}")
                print_info(f"Response: {response.text[:200]}")
                return False
    except Exception as e:
        print_warning(f"VoiceLive config endpoint test error: {e}")
        return True  # Not critical

async def validate_endpoint_format(endpoint: str) -> dict:
    """Validate VoiceLive endpoint format."""
    print_header("Validating Endpoint Format")
    
    result = {
        "valid": False,
        "type": None,
        "has_project": False,
        "issues": []
    }
    
    if not endpoint:
        result["issues"].append("Endpoint is empty")
        print_error("Endpoint is empty")
        return result
    
    endpoint_lower = endpoint.lower()
    
    # Check for unified endpoint
    if "services.ai.azure.com" in endpoint_lower:
        result["type"] = "unified"
        print_success("Endpoint type: Unified (services.ai.azure.com)")
        
        # Check for project name in path
        if "/api/projects/" in endpoint_lower:
            result["has_project"] = True
            print_success("Project-based unified endpoint detected")
        else:
            print_info("Standard unified endpoint (no project in path)")
            
    # Check for direct OpenAI endpoint
    elif "openai.azure.com" in endpoint_lower:
        result["type"] = "direct"
        print_success("Endpoint type: Direct (openai.azure.com)")
    else:
        result["issues"].append(f"Unknown endpoint format: {endpoint}")
        print_warning(f"Unknown endpoint format: {endpoint}")
        return result
    
    # Validate URL format
    if not endpoint.startswith("https://"):
        result["issues"].append("Endpoint should start with https://")
        print_error("Endpoint should use HTTPS")
    else:
        print_success("Endpoint uses HTTPS")
    
    # Check for trailing slash
    if endpoint.endswith("/"):
        print_info("Endpoint has trailing slash (OK)")
    else:
        print_info("Endpoint has no trailing slash (OK)")
    
    result["valid"] = len(result["issues"]) == 0
    return result

async def test_websocket_proxy_readiness(backend_url: str) -> bool:
    """Test if WebSocket proxy endpoint is accessible."""
    print_header("Testing WebSocket Proxy Readiness")
    
    try:
        # Try to connect to WebSocket endpoint (just check if it exists)
        async with httpx.AsyncClient(timeout=5.0) as client:
            # WebSocket endpoints typically return 400 or 426 for HTTP GET
            # We just want to see if the endpoint exists
            ws_url = backend_url.replace("https://", "wss://").replace("http://", "ws://")
            ws_endpoint = f"{ws_url}/api/v1/voice/voicelive/test-session"
            
            # Try HTTP GET first to see if endpoint exists
            response = await client.get(f"{backend_url}/api/v1/voice/voicelive/test-session")
            
            if response.status_code in [400, 426, 404]:
                # 400/426 = WebSocket upgrade required (endpoint exists)
                # 404 = endpoint doesn't exist
                if response.status_code == 404:
                    print_warning("WebSocket proxy endpoint not found (may need session ID)")
                else:
                    print_success(f"WebSocket proxy endpoint exists (status: {response.status_code})")
                return True
            elif response.status_code == 200:
                print_success("WebSocket proxy endpoint accessible")
                return True
            else:
                print_warning(f"WebSocket proxy endpoint returned: {response.status_code}")
                return True  # Not a critical failure
    except Exception as e:
        print_warning(f"WebSocket proxy test error: {e}")
        return True  # Not critical for validation

async def generate_validation_report(
    env_results: dict,
    health_ok: bool,
    config_ok: bool,
    endpoint_validation: dict,
    ws_ok: bool,
    backend_url: str
) -> dict:
    """Generate comprehensive validation report."""
    print_header("Validation Summary")
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "backend_url": backend_url,
        "environment_variables": {
            "all_required_present": env_results["all_present"],
            "required_vars": list(env_results["required"].keys()),
            "optional_vars": list(env_results["optional"].keys()),
            "missing_required": env_results["missing_required"]
        },
        "endpoint_validation": endpoint_validation,
        "health_check": health_ok,
        "config_endpoint": config_ok,
        "websocket_proxy": ws_ok,
        "overall_status": "PASS" if (
            env_results["all_present"] and
            health_ok and
            endpoint_validation["valid"]
        ) else "FAIL"
    }
    
    # Print summary
    print(f"\n{Colors.BOLD}Overall Status:{Colors.RESET} ", end="")
    if report["overall_status"] == "PASS":
        print_success("PASS - Configuration is valid")
    else:
        print_error("FAIL - Configuration has issues")
    
    print(f"\n{Colors.BOLD}Details:{Colors.RESET}")
    print(f"  Environment Variables: {'✅' if env_results['all_present'] else '❌'}")
    print(f"  Endpoint Format: {'✅' if endpoint_validation['valid'] else '❌'}")
    print(f"  Backend Health: {'✅' if health_ok else '❌'}")
    print(f"  WebSocket Proxy: {'✅' if ws_ok else '⚠️'}")
    
    if env_results["missing_required"]:
        print(f"\n{Colors.RED}Missing Required Variables:{Colors.RESET}")
        for var in env_results["missing_required"]:
            print(f"  - {var}")
    
    if endpoint_validation.get("issues"):
        print(f"\n{Colors.YELLOW}Endpoint Issues:{Colors.RESET}")
        for issue in endpoint_validation["issues"]:
            print(f"  - {issue}")
    
    return report

async def main():
    """Main validation function."""
    print_header("VoiceLive Backend Configuration Validation")
    
    # Get configuration from environment or Azure
    app_name = os.getenv("AZURE_CONTAINER_APP_NAME", "staging-env-api")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP", "engram-rg")
    backend_url = os.getenv("BACKEND_URL")
    
    if not backend_url:
        # Try to get from Azure
        print_info("Getting backend URL from Azure...")
        try:
            import subprocess
            cmd = [
                "az", "containerapp", "show",
                "--name", app_name,
                "--resource-group", resource_group,
                "--query", "properties.configuration.ingress.fqdn",
                "-o", "tsv"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            fqdn = result.stdout.strip()
            if fqdn:
                backend_url = f"https://{fqdn}"
                print_success(f"Backend URL: {backend_url}")
            else:
                print_error("Could not determine backend URL")
                sys.exit(1)
        except Exception as e:
            print_error(f"Failed to get backend URL: {e}")
            print_info("Set BACKEND_URL environment variable or ensure Azure CLI is configured")
            sys.exit(1)
    
    print_info(f"Container App: {app_name}")
    print_info(f"Resource Group: {resource_group}")
    print_info(f"Backend URL: {backend_url}")
    
    # Run validations
    env_results = await validate_environment_variables(app_name, resource_group)
    
    # Get endpoint for validation
    endpoint = env_results["required"].get("AZURE_VOICELIVE_ENDPOINT")
    endpoint_validation = await validate_endpoint_format(endpoint) if endpoint else {"valid": False, "issues": ["Endpoint not found"]}
    
    health_ok = await test_backend_health(backend_url)
    config_ok = await test_voicelive_config_endpoint(backend_url)
    ws_ok = await test_websocket_proxy_readiness(backend_url)
    
    # Generate report
    report = await generate_validation_report(
        env_results,
        health_ok,
        config_ok,
        endpoint_validation,
        ws_ok,
        backend_url
    )
    
    # Save report
    report_file = f"voicelive-backend-validation-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{Colors.BLUE}Validation report saved to: {report_file}{Colors.RESET}")
    
    # Exit with appropriate code
    sys.exit(0 if report["overall_status"] == "PASS" else 1)

if __name__ == "__main__":
    asyncio.run(main())

