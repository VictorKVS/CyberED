import json, os, subprocess, threading, uuid, shutil, re
from pathlib import Path
from model_zoo import discover, load_ollama
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

ROOT=Path(__file__).resolve().parent
REPORTS=ROOT/"reports"
REPORTS.mkdir(exist_ok=True)
STATE={"status":"idle","job":None,"current":None,"results":{},"report":None,"selected":[],"modules":{},"completed":0,"total":0}
LOCK=threading.Lock()

def command(args, timeout=25):
    if not shutil.which(args[0]):
        return {"status":"unavailable","reason":"executable not found"}
    try:
        p=subprocess.run(args, capture_output=True, text=True, errors="replace",
                         timeout=timeout, stdin=subprocess.DEVNULL,
                         creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        return {"status":"ok" if p.returncode==0 else "error",
                "exit_code":p.returncode,"stdout":p.stdout[:120000],"stderr":p.stderr[:3000]}
    except FileNotFoundError:
        return {"status":"unavailable","reason":"executable not found"}
    except subprocess.TimeoutExpired:
        return {"status":"timeout"}
    except Exception as exc:
        return {"status":"error","reason":str(exc)}

def ps(script):
    return command(["powershell.exe","-NoProfile","-NonInteractive","-Command",script],40)

def scan(job, requested=None):
    tasks=[
      ("hardware",lambda:ps("Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,TotalPhysicalMemory,HypervisorPresent | ConvertTo-Json -Compress; Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json -Compress")),
      ("windows",lambda:ps("Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber | ConvertTo-Json -Compress")),
      ("disks",lambda:ps("Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Select-Object DeviceID,Size,FreeSpace | ConvertTo-Json -Compress")),
      ("software",lambda:ps("$p=@('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'); Get-ItemProperty $p -ErrorAction SilentlyContinue | Where-Object DisplayName | Select-Object DisplayName,DisplayVersion,Publisher | ConvertTo-Json -Compress")),
      ("aida64",lambda:ps("$p='C:\\Program Files\\FinalWire\\AIDA64 Extreme'; if(Test-Path $p){Get-ChildItem $p -Filter '*.exe' -File | Select-Object Name,FullName,@{N='Version';E={$_.VersionInfo.ProductVersion}} | ConvertTo-Json -Compress}else{'NOT_FOUND'}")),
      ("docker",lambda:command(["docker","version","--format","{{json .}}"])),
      ("containers",lambda:command(["docker","ps","-a","--format","{{json .}}"])),
      ("wsl",lambda:command(["wsl.exe","--list","--verbose"])),
      ("virtualization",lambda:ps("@(Get-Service -Name vmms,vmcompute,hns -ErrorAction SilentlyContinue | Select-Object Name,Status,StartType) | ConvertTo-Json -Compress")),
      ("adapters",lambda:ps("Get-NetAdapter | Select-Object Name,Status,LinkSpeed | ConvertTo-Json -Compress")),
      ("network",lambda:ps("Get-NetIPConfiguration | Select-Object InterfaceAlias,IPv4Address,IPv4DefaultGateway,DNSServer | ConvertTo-Json -Depth 5 -Compress")),
    ]
    if requested is not None:
        tasks=[t for t in tasks if t[0] in requested]
    with LOCK:
        STATE["total"]=len(tasks)
        STATE["completed"]=0
        STATE["modules"]={name:"pending" for name,_ in tasks}
    try:
        results={}
        for name,fn in tasks:
            with LOCK:
                STATE["current"]=name
                STATE["modules"][name]="running"
            result=fn()
            if name in ("docker","containers") and result["status"] == "error":
                result["hint"]="Docker CLI доступен, но команда завершилась ошибкой. Проверьте Docker Desktop, контекст и права доступа; TIMA ничего не изменяет."
            if name == "virtualization" and result["status"] == "error":
                result["hint"]="Не удалось прочитать состояние служб. Проверьте доступность Get-Service и права пользователя."
            results[name]=result
            with LOCK:
                STATE["results"]=dict(results)
                STATE["modules"][name]=result.get("status","error")
                STATE["completed"]+=1
        report={"job":job,"timestamp":datetime.now(timezone.utc).isoformat(),
                "scope":"local host passive inventory; no network scanning","results":results}
        filename="inventory_"+job+".json"
        (REPORTS/filename).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        with LOCK: STATE.update(status="complete",current=None,report=filename)
    except Exception as exc:
        with LOCK: STATE.update(status="failed",current=None,error=str(exc))

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def reply(self,code,data,ctype="application/json"):
        raw=data.encode("utf-8") if isinstance(data,str) else json.dumps(data,ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type",ctype+"; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.end_headers()
        self.wfile.write(raw)
    def do_GET(self):
        if self.path=="/":
            return self.reply(200,(ROOT/"index.html").read_text(encoding="utf-8"),"text/html")
        if self.path=="/api/models":
            return self.reply(200,discover())
        if self.path=="/api/modules":
            return self.reply(200,{"modules":["hardware","windows","disks","software","aida64","docker","containers","wsl","virtualization","adapters","network"]})
        if self.path=="/api/status":
            with LOCK: value=dict(STATE)
            return self.reply(200,value)
        if self.path=="/api/summary":
            with LOCK: name=STATE.get("report")
            if not name: return self.reply(404,{"error":"no report"})
            report=json.loads((REPORTS/name).read_text(encoding="utf-8"))
            summary={"schema":"tima-public-summary-v1","scope":report.get("scope"),
                     "timestamp":report.get("timestamp"),"modules":{}}
            for key,value in report.get("results",{}).items():
                summary["modules"][key]={"status":value.get("status","unknown")}
            summary["publication_status"]="NOT_PUBLISHED_REVIEW_REQUIRED"
            return self.reply(200,summary)
        if self.path=="/api/report":
            with LOCK: name=STATE.get("report")
            if not name: return self.reply(404,{"error":"no report"})
            return self.reply(200,(REPORTS/name).read_text(encoding="utf-8"))
        return self.reply(404,{"error":"not found"})
    def do_POST(self):
        from urllib.parse import urlsplit, parse_qs
        parsed=urlsplit(self.path)
        if parsed.path=="/api/models/load":
            if self.headers.get("Origin")!="http://127.0.0.1:8093":
                return self.reply(403,{"error":"origin denied"})
            try:
                length=int(self.headers.get("Content-Length","0"))
                if not 0<length<=500: return self.reply(400,{"error":"invalid body length"})
                data=json.loads(self.rfile.read(length))
                code,result=load_ollama(data.get("name"))
                return self.reply(code,result)
            except (ValueError,TypeError,AttributeError):
                return self.reply(400,{"error":"invalid JSON"})
        if parsed.path!="/api/scan": return self.reply(404,{"error":"not found"})
        query=parse_qs(parsed.query)
        allowed={"hardware","windows","disks","software","aida64","docker","containers","wsl","virtualization","adapters","network"}
        selected=query.get("module",[])
        if len(selected)>1 or (selected and selected[0] not in allowed):
            return self.reply(400,{"error":"invalid module"})
        if self.headers.get("Origin")!= "http://127.0.0.1:8093":
            return self.reply(403,{"error":"origin denied"})
        if self.headers.get("Content-Length","0") not in ("0",""):
            return self.reply(400,{"error":"body not allowed"})
        with LOCK:
            if STATE["status"]=="running": return self.reply(409,{"error":"busy"})
            job=uuid.uuid4().hex[:12]
            STATE.update(status="running",job=job,current="starting",results={},report=None,error=None,completed=0,total=0,modules={})
        threading.Thread(target=scan,args=(job,selected or None),daemon=True).start()
        return self.reply(202,{"job":job})
if __name__=="__main__":
    if os.name!="nt": raise SystemExit("Windows only")
    print("TIMA Control Center: http://127.0.0.1:8093")
    ThreadingHTTPServer(("127.0.0.1",8093),Handler).serve_forever()
