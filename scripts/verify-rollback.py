"""Exercise a failed replacement and restore the known-good image on a CI host."""
import json
import os
import subprocess
import urllib.request

compose = ["docker", "compose", "--project-name", "project05-demo"]
good = os.environ["PROJECT_IMAGE"]
bad = good + "-broken"
good_id = json.loads(subprocess.check_output(["docker", "image", "inspect", good], text=True))[0]["Id"]
subprocess.run(["docker", "build", "--tag", bad, "-"],
               input=f'FROM {good}\nCMD ["node", "-e", "process.exit(1)"]\n',
               text=True, check=True)

def inspect_container():
    container = subprocess.check_output(compose + ["ps", "--all", "--quiet", "app"], text=True).strip()
    if not container:
        raise RuntimeError("Compose application container missing")
    return json.loads(subprocess.check_output(["docker", "inspect", container], text=True))[0]

print("Attempting the intentionally broken candidate", flush=True)
try:
    failed = subprocess.run(compose + ["up", "--detach", "--wait", "--wait-timeout", "30"],
                            env=dict(os.environ, PROJECT_IMAGE=bad), text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(failed.stdout, flush=True)
    candidate = inspect_container()
    if failed.returncode == 0:
        raise RuntimeError("The broken candidate unexpectedly passed deployment")
    if candidate["Config"]["Image"] != bad or candidate["State"]["ExitCode"] != 1:
        raise RuntimeError("Failure did not originate from the intended broken candidate")
    print("PASS: deployment rejected the intended failed candidate", flush=True)
finally:
    print("Restoring the known-good commit image", flush=True)
    subprocess.run(compose + ["up", "--detach", "--wait", "--wait-timeout", "60"],
                   env=dict(os.environ, PROJECT_IMAGE=good), check=True)

restored = inspect_container()
if restored["Image"] != good_id or restored["State"]["Health"]["Status"] != "healthy":
    raise RuntimeError("Rollback did not restore the healthy original image ID")
with urllib.request.urlopen("http://127.0.0.1:13000/health", timeout=5) as response:
    if json.load(response) != {"status": "healthy"}:
        raise RuntimeError("Health endpoint did not recover")
print("PASS: original image ID restored, Docker health healthy, HTTP recovered.")
