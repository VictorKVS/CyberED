"""FATHER Model Zoo: read-only local discovery and explicit Ollama model load.
No recursive scan of whole drives, no downloads, no external network calls.
"""
import os, json, shutil, subprocess, urllib.request, urllib.error
from pathlib import Path

EXTENSIONS={".gguf",".safetensors",".onnx",".pt",".pth",".ckpt"}
MAX_FILES=20000
MAX_DEPTH=9

def roots():
    home=Path.home()
    candidates=[
        home/".ollama"/"models",
        home/".cache"/"huggingface"/"hub",
        home/".cache"/"lm-studio"/"models",
        home/"AppData"/"Local"/"LM-Studio"/"models",
        Path("G:/1"),
        home/"models",
        home/"Downloads",
        home/"AppData"/"Local"/"Ollama"/"models",
        Path("G:/models"),
        Path("G:/Models"),
        Path("G:/LLM"),
        Path("G:/AI"),
        Path("D:/models"),
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
    models, warnings, checked_roots, sources = [], [], [], []
    inspected=0
    for root in roots():
        checked_roots.append(str(root))
        root_count=0
        stack=[(root,0)]
        truncated=False
        while stack:
            if root_count>=MAX_FILES:
                truncated=True
                break
            folder,depth=stack.pop()
            try:
                with os.scandir(folder) as entries:
                    for entry in entries:
                        root_count+=1
                        inspected+=1
                        if root_count>=MAX_FILES:
                            truncated=True
                            break
                        try:
                            if entry.is_symlink():
                                continue
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
            except (PermissionError,OSError):
                warnings.append("Unreadable directory under "+str(root))
        sources.append({"root":str(root),"inspected":root_count,"truncated":truncated})
        if truncated:
            warnings.append("Search limit reached in "+str(root)+"; other roots continue")
    ollama=[]
    # Ollama model manifests are JSON records; blob filenames have no model extension.
    # Read only metadata, never read or publish model blobs.
    seen_models=set()
    for root in roots():
        manifest_base=root/"manifests"
        if not manifest_base.is_dir():
            continue
        for registry in manifest_base.iterdir():
            if not registry.is_dir() or registry.is_symlink(): continue
            for namespace in registry.iterdir():
                if not namespace.is_dir() or namespace.is_symlink(): continue
                for model_dir in namespace.iterdir():
                    if not model_dir.is_dir() or model_dir.is_symlink(): continue
                    for tag in model_dir.iterdir():
                        if not tag.is_file() or tag.is_symlink(): continue
                        name=model_dir.name+":"+tag.name
                        if name not in seen_models:
                            seen_models.add(name)
                            ollama.append({"name":name,"status":"manifest-found-not-tested",
                                           "runtime":"ollama","location":str(tag.parent),
                                           "registry":registry.name,"namespace":namespace.name})
    if shutil.which("ollama"):
        try:
            p=subprocess.run(["ollama","list"],capture_output=True,text=True,timeout=12,
                             creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            if p.returncode==0:
                for line in p.stdout.splitlines()[1:]:
                    parts=line.split()
                    if parts:
                        if parts[0] in seen_models:
                            for item in ollama:
                                if item["name"]==parts[0]: item["status"]="installed"
                        else:
                            seen_models.add(parts[0])
                            ollama.append({"name":parts[0],"status":"installed","runtime":"ollama"})
            else:
                warnings.append("Ollama CLI failed: "+p.stderr[:180])
        except (OSError,subprocess.TimeoutExpired):
            warnings.append("Ollama list timed out or failed")
    else:
        warnings.append("Ollama CLI not found on PATH")
    return {"files":models,"ollama":ollama,"roots_checked":len(checked_roots),
            "checked_roots":checked_roots,"sources":sources,"inspected":inspected,
            "warnings":warnings,"search_complete":not any(x["truncated"] for x in sources),
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
