#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse

# Configuration
VENV_NAME = ".venv"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
APP_NAME = "msx-flask"

SERVERS = {
    "dev": {
        "host": "mm",
        "branch": "develop",
        "path": f"/data/websites/{APP_NAME}",
        "user": APP_NAME,
    },
    "prd": {
        "host": "mm3",
        "branch": "develop", # Can be changed to main later
        "path": f"/data/websites/{APP_NAME}",
        "user": APP_NAME,
    },
}

def print_step(msg): print(f"\n🔵 [STEP] {msg}")
def print_success(msg): print(f"✅ {msg}")
def print_error(msg): print(f"❌ [ERROR] {msg}")
def print_info(msg): print(f"ℹ️  {msg}")
def print_cmd(msg): print(f"   $ {msg}")

def run_command(command, cwd=None, quiet=False, capture_output=False):
    try:
        if capture_output:
            return subprocess.check_output(command, shell=True, cwd=cwd, text=True)
        if quiet:
            subprocess.run(command, shell=True, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            subprocess.check_call(command, shell=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        if quiet and not capture_output:
            print_error(f"Command failed: {command}")
            if e.stdout:
                print("--- Output ---")
                print(e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout)
        elif not capture_output:
            print_error(f"Error running command: {command}")
        return "" if capture_output else False

def ssh_command(server_conf, cmd, quiet=False):
    escaped_cmd = cmd.replace("'", "'\\''")
    remote_command = f"sudo -u {server_conf['user']} -- sh -c 'cd {server_conf['path']} && {escaped_cmd}'"
    ssh_cmd = f"ssh {server_conf['host']} \"{remote_command}\""
    if not quiet:
        print_cmd(f"[{server_conf['host']}] {cmd}")
    return run_command(ssh_cmd, quiet=quiet)

def ssh_command_direct(host, cmd, quiet=False, capture_output=False):
    ssh_cmd = f"ssh {host} \"{cmd}\""
    if not quiet:
        print_cmd(f"[{host}] {cmd}")
    return run_command(ssh_cmd, quiet=quiet, capture_output=capture_output)

def restart_server(env):
    conf = SERVERS[env]
    print_step(f"Restarting {APP_NAME} on {conf['host']} via OpenRC...")
    ssh_command_direct(conf['host'], f"sudo /sbin/rc-service {APP_NAME} restart", quiet=True)
    print_success("Restart command sent")

def deploy(env):
    if env not in SERVERS:
        print_error(f"Unknown environment: {env}")
        sys.exit(1)
    conf = SERVERS[env]
    print(f"\n🚀 === Deploying {APP_NAME} to {env.upper()} ({conf['host']}) === 🚀")

    # Activate maintenance mode
    print_step("Activating Maintenance Mode...")
    ssh_command(conf, "touch maintenance.flag", quiet=True)

    try:
        print_step(f"Updating Remote Server ({conf['host']})")
        if not ssh_command(conf, f"git checkout {conf['branch']} && git pull", quiet=True):
            print_error("Failed to update git on remote server")
            sys.exit(1)
        print_success("Git pulled successfully")

        print_step("Updating Dependencies (Remote)")
        if not ssh_command(conf, f"{VENV_NAME}/bin/python -m pip install -r requirements.txt", quiet=True):
            print_error("pip install had issues")
        else:
            print_success("Dependencies updated")

        restart_server(env)
    finally:
        # Deactivate maintenance mode
        print_step("Deactivating Maintenance Mode...")
        ssh_command(conf, "rm -f maintenance.flag", quiet=True)

    print(f"\n✨ Deployment to {env.upper()} Complete! ✨\n")

def local_start():
    port = 5000
    print_step(f"Starting local Flask server on port {port}...")
    venv_path = os.path.join(PROJECT_ROOT, VENV_NAME)
    flask_cmd = os.path.join(venv_path, "bin", "flask")
    run_command(f'"{flask_cmd}" run --host=0.0.0.0 --port={port} --debug --reload', cwd=PROJECT_ROOT)

def main():
    parser = argparse.ArgumentParser(description=f"Manage {APP_NAME}")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("start", help="Start local dev server")
    
    p_deploy = subparsers.add_parser("deploy", help="Deploy to environment")
    p_deploy.add_argument("env", choices=["dev", "prd"], help="Environment to deploy to")
    
    p_restart = subparsers.add_parser("restart", help="Restart application service")
    p_restart.add_argument("env", choices=["dev", "prd"], help="Target environment")

    args = parser.parse_args()

    if args.command == "start":
        local_start()
    elif args.command == "deploy":
        deploy(args.env)
    elif args.command == "restart":
        restart_server(args.env)
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Operation cancelled.")
        sys.exit(130)
