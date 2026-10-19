"""Deploy twice, check the real container, require an unchanged second pass."""
import json
import os
import re
import subprocess
import urllib.request

command = ["ansible-playbook", "-i", "ansible/inventory.ini", "ansible/site.yml"]
compose = ["docker", "compose", "--project-name", "project05-demo"]
for attempt in (1, 2):
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            env=dict(os.environ, ANSIBLE_NOCOLOR="1"))
    print(f"=== Deployment {attempt} ===\n{result.stdout}", flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
    recap = re.search(r"localhost\s+:\s+ok=\d+\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)", result.stdout)
    if not recap or any(int(recap[i]) for i in (2, 3)):
        raise SystemExit("Deployment recap missing or unsuccessful")
    if attempt == 2 and int(recap[1]):
        raise SystemExit("Second deployment unexpectedly changed resources")
container = subprocess.check_output(compose + ["ps", "--quiet", "app"], text=True).strip()
if not container:
    raise SystemExit("Application container missing")
info = json.loads(subprocess.check_output(["docker", "inspect", container], text=True))[0]
assert info["State"]["Health"]["Status"] == "healthy"
assert info["Config"]["Image"] == os.environ["PROJECT_IMAGE"]
assert info["HostConfig"]["ReadonlyRootfs"] is True
assert info["HostConfig"]["PortBindings"]["3000/tcp"] == [{"HostIp": "127.0.0.1", "HostPort": "13000"}]
uid = subprocess.check_output(["docker", "exec", container, "id", "-u"], text=True).strip()
assert uid != "0", "Container must run as a non-root user"
with urllib.request.urlopen("http://127.0.0.1:13000/", timeout=5) as response:
    assert json.load(response)["environment"] == "production"
print("PASS: healthy commit-tagged container, non-root, read-only, loopback and unchanged redeployment.")
