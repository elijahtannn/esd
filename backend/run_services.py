import subprocess
import sys
import os
from pathlib import Path

def run_services():
    # Define service commands
    services = [
        {
            "name": "Ticket Service",
            "command": ["python", "ticket_service/app.py"],
            "cwd": "."
        },
        {
            "name": "User Service",
            "command": ["python", "user_service.py"],
            "cwd": "."
        },
        {
            "name": "Validation Service",
            "command": ["python", "validate_ticket.py"],
            "cwd": "."
        },
        {
            "name": "Transfer Service",
            "command": ["python", "transfer.py"],
            "cwd": "."
        },
        {
            "name": "Order Service",
            "command": ["python", "order_service.py"],
            "cwd": "."
        }
    ]

    processes = []
    
    try:
        # Start each service
        for service in services:
            print(f"Starting {service['name']}...")
            process = subprocess.Popen(
                service["command"],
                cwd=service["cwd"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes.append({"process": process, "name": service["name"]})
            print(f"{service['name']} started!")

        # Keep the script running and monitor output
        while True:
            for p in processes:
                output = p["process"].stdout.readline()
                if output:
                    print(f"[{p['name']}] {output.strip()}")
                
                error = p["process"].stderr.readline()
                if error:
                    print(f"[{p['name']} ERROR] {error.strip()}", file=sys.stderr)

                # Check if process has terminated
                if p["process"].poll() is not None:
                    print(f"{p['name']} has terminated!")
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        print("\nShutting down all services...")
        for p in processes:
            p["process"].terminate()
        
        # Wait for all processes to terminate
        for p in processes:
            p["process"].wait()
        
        print("All services have been shut down.")

if __name__ == "__main__":
    run_services()