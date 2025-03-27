#!/usr/bin/env python3
import os
import subprocess
import sys
from typing import List, Optional

# ANSI color codes
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"

def print_colored(text: str, color: str) -> None:
    """Print text in specified color."""
    print(f"{color}{text}{RESET}")

def has_docker_compose(directory: str) -> bool:
    """Check if a directory has a docker-compose.yml file."""
    return os.path.exists(os.path.join(directory, "docker-compose.yml"))

def run_command(command: List[str], cwd: Optional[str] = None) -> bool:
    """Run a shell command and return True if successful."""
    try:
        subprocess.run(command, cwd=cwd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def start_services() -> None:
    """Start all Docker services."""
    print_colored("Starting all Docker services...", GREEN)
    
    # Start API Gateway
    if has_docker_compose("api_gateway"):
        print_colored("Starting API Gateway...", GREEN)
        run_command(["docker-compose", "up", "-d"], "api_gateway")

    # Start Atomic Services
    atomic_services_dir = "atomic_services"
    if os.path.exists(atomic_services_dir):
        for service in os.listdir(atomic_services_dir):
            service_path = os.path.join(atomic_services_dir, service)
            if os.path.isdir(service_path) and has_docker_compose(service_path):
                print_colored(f"Starting {service}...", GREEN)
                run_command(["docker-compose", "up", "-d"], service_path)

    # Start Composite Services
    composite_services_dir = "composite_services"
    if os.path.exists(composite_services_dir):
        for service in os.listdir(composite_services_dir):
            service_path = os.path.join(composite_services_dir, service)
            if os.path.isdir(service_path) and has_docker_compose(service_path):
                print_colored(f"Starting {service}...", GREEN)
                run_command(["docker-compose", "up", "-d"], service_path)

    print_colored("All services started!", GREEN)

def stop_services() -> None:
    """Stop all Docker services."""
    print_colored("Stopping all Docker services...", RED)
    
    # Stop Composite Services first
    composite_services_dir = "composite_services"
    if os.path.exists(composite_services_dir):
        for service in os.listdir(composite_services_dir):
            service_path = os.path.join(composite_services_dir, service)
            if os.path.isdir(service_path) and has_docker_compose(service_path):
                print_colored(f"Stopping {service}...", RED)
                run_command(["docker-compose", "down"], service_path)

    # Stop Atomic Services
    atomic_services_dir = "atomic_services"
    if os.path.exists(atomic_services_dir):
        for service in os.listdir(atomic_services_dir):
            service_path = os.path.join(atomic_services_dir, service)
            if os.path.isdir(service_path) and has_docker_compose(service_path):
                print_colored(f"Stopping {service}...", RED)
                run_command(["docker-compose", "down"], service_path)

    # Stop API Gateway last
    if has_docker_compose("api_gateway"):
        print_colored("Stopping API Gateway...", RED)
        run_command(["docker-compose", "down"], "api_gateway")

    print_colored("All services stopped!", RED)

def print_usage() -> None:
    """Print usage instructions."""
    print("Usage: python docker_manage.py {start|stop}")
    print("  start - Start all Docker services")
    print("  stop  - Stop all Docker services")

def main() -> None:
    """Main entry point."""
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]
    if command == "start":
        start_services()
    elif command == "stop":
        stop_services()
    else:
        print_usage()
        sys.exit(1)

if __name__ == "__main__":
    main() 