import json, os, platform, subprocess, threading, uuid, shutil
from pathlib import Path
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

ROOT=Path(__file__).resolve().parent
REPORTS=ROOT/"reports"
REPORTS.mkdir(exist_ok=True)
STATE={"status":"idle","job":None,"current":None,"results":{},"report":None}
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
    except subprocess.TimeoutExpired:
        return {"status":"timeout"}
    except Exception as exc:
        return {"status":"error","reason":str(exc)}

def ps(script):
    return command(["powershell.exe","-NoProfile","-NonInteractive","-Command",script],40)

def scan(job):
    tasks=[
      ("hardware",lambda:ps("Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,TotalPhysicalMemory,HypervisorPresent | ConvertTo-Json -Compress; Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json -Compress")),
      ("windows",lambda:ps("Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber | ConvertTo-Json -Compress")),
      ("disks",lambda:ps("Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Select-Object DeviceID,Size,FreeSpace | ConvertTo-Json -Compress")),
      ("software",lambda:ps("$p=@('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'); Get-ItemProperty $p -ErrorAction SilentlyContinue | Where-Object DisplayName | Select-Object DisplayName,DisplayVersion,Publisher | ConvertTo-Json -Compress")),
      ("aida64",lambda:ps("$p='C:\\Program Files\\FinalWire\\AIDA64 Extreme'; if(Test-Path $p){Get-ChildItem $p -Filter '*.exe' -File | Select-Object Name,FullName,@{N='Version';E={$_.VersionInfo.ProductVersion}} | ConvertTo-Json -Compress}else{'NOT_FOUND'}")),
      ("docker",lambda:command(["docker","version","--format","{{json .}}"])),
      ("containers",lambda:command(["docker","ps","-a","--format","{{json .}}"])),
      ("wsl",lambda:command(["wsl.exe","--list","--verbose"])),
      ("virtualization",lambda:ps("Get-Service vmms,vmcompute,hns -ErrorAction SilentlyContinue | Select-Object Name,Status,StartType | ConvertTo-Json -Compress")),
      ("adapters",lambda:ps("Get-NetAdapter | Select-Object Name,Status,LinkSpeed | ConvertTo-Json -Compress")),
      ("network",lambda:ps("Get-NetIPConfiguration | Select-Object InterfaceAlias,IPv4Address,IPv4DefaultGateway,DNSServer | ConvertTo-Json -Depth 5 -Compress")),
    ]
    try:
        results={}
        for name,fn in tasks:
            with LOCK: STATE["current"]=name
            results[name]=fn()
            with LOCK: STATE["results"]=dict(results)
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
        if self.path=="/api/status":
            with LOCK: value=dict(STATE)
            return self.reply(200,value)
        if self.path=="/api/report":
            with LOCK: name=STATE.get("report")
            if not name: return self.reply(404,{"error":"no report"})
            return self.reply(200,(REPORTS/name).read_text(encoding="utf-8"))
        return self.reply(404,{"error":"not found"})
    def do_POST(self):
        if self.path!="/api/scan": return self.reply(404,{"error":"not found"})
        if self.headers.get("Origin")!= "http://127.0.0.1:8093":
            return self.reply(403,{"error":"origin denied"})
        if self.headers.get("Content-Length","0") not in ("0",""):
            return self.reply(400,{"error":"body not allowed"})
        with LOCK:
            if STATE["status"]=="running": return self.reply(409,{"error":"busy"})
            job=uuid.uuid4().hex[:12]
            STATE.update(status="running",job=job,current="starting",results={},report=None,error=None)
        threading.Thread(target=scan,args=(job,),daemon=True).start()
        return self.reply(202,{"job":job})
if __name__=="__main__":
    if os.name!="nt": raise SystemExit("Windows only")
    print("TIMA Control Center: http://127.0.0.1:8093")
    ThreadingHTTPServer(("127.0.0.1",8093),Handler).serve_forever()
