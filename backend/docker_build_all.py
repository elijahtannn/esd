import os
import subprocess
from pathlib import Path

def find_docker_compose_files(root_dir):
    """Find all docker-compose.yml files in the given directory and its subdirectories."""
    compose_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file in ('docker-compose.yml', 'docker-compose.yaml'):
                compose_files.append(os.path.join(root, file))
    return compose_files

def build_service(compose_file):
    """Build services defined in the docker-compose file."""
    try:
        print(f"\nBuilding services in {compose_file}...")
        result = subprocess.run(
            ['docker-compose', '-f', compose_file, 'build'],
            check=True,
            capture_output=True,
            encoding='utf-8'  # Explicitly use UTF-8 encoding
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building {compose_file}:")
        print(e.stderr)
        return False

def main():
    # Get the current directory (backend folder)
    backend_dir = Path(__file__).parent.absolute()
    
    # Find all docker-compose files
    compose_files = find_docker_compose_files(backend_dir)
    
    if not compose_files:
        print("No docker-compose files found!")
        return
    
    print(f"Found {len(compose_files)} docker-compose files:")
    for file in compose_files:
        print(f"- {file}")
    
    # Build all services
    print("\nStarting build process...")
    success_count = 0
    
    for compose_file in compose_files:
        if build_service(compose_file):
            success_count += 1
    
    print(f"\nBuild complete! Successfully built {success_count}/{len(compose_files)} services.")

if __name__ == "__main__":
    main() 