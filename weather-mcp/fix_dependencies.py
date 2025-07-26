#!/usr/bin/env python3
"""
Script to fix dependencies for Weekly Weather MCP
"""
import subprocess
import sys
import os

def run_command(command):
    """Run a shell command and print output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result.returncode == 0

def main():
    """Fix dependencies for the project"""
    print("Fixing dependencies for Weekly Weather MCP...")
    
    # Uninstall problematic packages first
    print("\n1. Uninstalling problematic packages...")
    run_command("pip uninstall -y pydantic pydantic-core")
    
    # Install older pydantic version first (required for OpenAI dependency)
    print("\n2. Installing older pydantic version...")
    run_command("pip install 'pydantic<2.0.0'")
    
    # Install openai and other dependencies
    print("\n3. Installing other dependencies...")
    dependencies = [
        "python-dotenv",
        "requests>=2.32.0",
        "openai",
        "langchain-openai",
        "langchain"
    ]
    
    for dep in dependencies:
        run_command(f"pip install {dep}")
    
    # Try to install mcp packages if available
    print("\n4. Attempting to install MCP packages (these might fail but are mocked in tests)...")
    run_command("pip install mcp-server fastmcp --no-deps")
    
    print("\nDependency installation complete. You can now run the tests.")
    print("To run test_client.py:")
    print("  python test_client.py")
    print("\nTo run test_mcp_client.py:")
    print("  python test_mcp_client.py")
    print("\nTo run test_mcp_integration.py:")
    print("  python test_mcp_integration.py")
    print("\nTo run test_weather_mcp.py:")
    print("  python test_weather_mcp.py")
    
if __name__ == "__main__":
    main()
