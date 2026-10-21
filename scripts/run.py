#!/usr/bin/env python3
"""Run builds and package tests in separate disposable target containers."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
targets = json.loads((ROOT / "targets.json").read_text())
p = argparse.ArgumentParser()
p.add_argument("target", choices=sorted(targets))
p.add_argument("--stage", choices=["all", "build", "test"], default="all")
args = p.parse_args()
target = targets[args.target]
output = ROOT / "out" / args.target
output.mkdir(parents=True, exist_ok=True)
if args.stage != "test":
    subprocess.check_call(["python3", str(ROOT / "scripts/fetch.py")])
revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT),
                                   stderr=subprocess.DEVNULL).decode().strip()
for stage in (["build", "test"] if args.stage == "all" else [args.stage]):
    command = ["docker", "run", "--rm", "--platform", "linux/amd64",
               "--cap-drop=ALL", "--cap-add=CHOWN", "--cap-add=DAC_OVERRIDE",
               "--cap-add=FOWNER", "--cap-add=SETGID", "--cap-add=SETUID",
               "--cap-add=KILL", "--security-opt=no-new-privileges",
               "-v", str(ROOT) + ":/repo:ro",
               "-v", str(output) + ":/out",
               "-e", "TARGET=" + args.target,
               "-e", "SOURCE_REVISION=" + revision,
               "-e", "JOBS=" + os.environ.get("JOBS", "4"),
               target["image"], "bash", "/repo/scripts/" + stage + ".sh"]
    with (output / (stage + ".log")).open("w") as log:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in iter(process.stdout.readline, b""):
            text = line.decode("utf-8", errors="replace")
            print(text, end="", flush=True)
            log.write(text)
        result = process.wait()
    if result:
        raise SystemExit(result)
    if stage == "test":
        subprocess.check_call(["python3", str(ROOT / "scripts/bundle.py"), args.target])
