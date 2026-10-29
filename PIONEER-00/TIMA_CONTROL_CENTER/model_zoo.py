"""FATHER Model Zoo: read-only local discovery and explicit Ollama model load.
No recursive scan of whole drives, no downloads, no external network calls.
"""
import os, json, shutil, subprocess, urllib.request, urllib.error
from pathlib import Path

EXTENSIONS={".gguf",".safetensors",".onnx",".pt",".pth",".ckpt"}
MAX_FILES=1500
MAX_DEPTH=5

def roots():
    home=Path.home()
    candidates=[
        home/".ollama"/"models",
        home/".cache"/"huggingface"/"hub",
        home/".cache"/"lm-studio"/"models",
        home/"AppData"/"Local"/"LM-Studio"/"models",
        Path("G:/1"),
    ]
    for var in ("FATHER_MODEL_DIRS",):
        for raw in os.environ.get(var,"").split(os.pathsep):
            if raw.strip(): candidates.append(Path(raw.strip()))
    seen=set()
    for p in candidates:
        try:
            resolved=p.resolve()
            if resolved.is_dir() and str(resolved).lower() not in seen:
                seen.add(str(resolved).lower())
                yield resolved
        except OSError:
            continue

def discover():
    models=[]
    warnings=[]
    inspected=0
    for root in roots():
        # Avoid expensive scans of all project code under G:/1; bounded depth/file count.
        stack=[(root,0)]
        while stack and inspected<MAX_FILES:
            folder,depth=stack.pop()
            try:
                with os.scandir(folder) as entries:
                    for entry in entries:
                        inspected+=1
                        if inspected>=MAX_FILES: break
                        try:
                            if entry.is_symlink(): continue
                            if entry.is_file(follow_symlinks=False):
                                suffix=Path(entry.name).suffix.lower()
                                if suffix in EXTENSIONS:
                                    stat=entry.stat(follow_symlinks=False)
                                    models.append({"id":"file:"+str(len(models)),"name":entry.name,
                                                   "format":suffix.lstrip("."),"size_gb":round(stat.st_size/1073741824,2),
                                                   "source":"local-file","location":str(Path(entry.path).parent),
                                                   "status":"found-not-tested"})
                            elif depth<MAX_DEPTH and entry.is_dir(follow_symlinks=False):
                                if entry.name.lower() not in {".git","node_modules",".venv","venv","__pycache__","reports","reports-public"}:
                                    stack.append((Path(entry.path),depth+1))
                        except (PermissionError,OSError):
                            continue
            except (PermissionError,OSError) as exc:
                warnings.append(str(type(exc).__name__))
        if inspected>=MAX_FILES:
            warnings.append("File inspection limit reached; results may be incomplete")
            break
    ollama=[]
    if shutil.which("ollama"):
        try:
            p=subprocess.run(["ollama","list"],capture_output=True,text=True,timeout=12,
                             creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            if p.returncode==0:
                for line in p.stdout.splitlines()[1:]:
                    parts=line.split()
                    if parts:
                        ollama.append({"name":parts[0],"status":"installed","runtime":"ollama"})
            else:
                warnings.append("Ollama CLI unavailable: "+p.stderr[:180])
        except (OSError,subprocess.TimeoutExpired):
            warnings.append("Ollama list timed out or failed")
    return {"files":models,"ollama":ollama,"roots_checked":sum(1 for _ in roots()),
            "inspected":inspected,"warnings":warnings,
            "note":"File discovery does not prove model compatibility or readiness"}

def load_ollama(name):
    if not isinstance(name,str) or not name or len(name)>180:
        return 400,{"error":"Invalid model name"}
    found=discover()["ollama"]
    if name not in {m["name"] for m in found}:
        return 404,{"error":"Model not found in local Ollama registry"}
    body=json.dumps({"model":name,"prompt":"","stream":False,"keep_alive":"5m"}).encode()
    req=urllib.request.Request("http://127.0.0.1:11434/api/generate",data=body,
                               headers={"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=90) as response:
            data=json.loads(response.read(1000000))
        return 200,{"status":"loaded","model":name,"done":data.get("done")}
    except (urllib.error.URLError,TimeoutError,OSError,ValueError) as exc:
        return 502,{"error":"Ollama load failed","detail":str(exc)[:250]}
