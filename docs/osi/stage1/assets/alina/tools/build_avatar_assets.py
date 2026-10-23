#!/usr/bin/env python3
"""Cut the 1536x1024 ALINA contact sheet into web-ready avatar frames.
Usage: python build_avatar_assets.py source.png --out ./alina
Requires Pillow. Keeps original intact. Layout tailored to source sheet.
"""
from pathlib import Path
from PIL import Image
import argparse, json

LABELS=[
"neutral","soft_smile","smile","speech_a","speech_b","speech_c","question","clarify","serious","look_side",
"listening","thinking","analyzing","reading","writing","explaining_1","explaining_2","inviting","warning","nod",
"approval","agreement","disagree","surprised","pondering","look_down","eyes_closed","eyes_open","blink_1","blink_2",
"blink_3","profile_left","profile_right","profile_speech","at_laptop","on_phone","with_documents","presenting_screen","final_pose"
]
# The generated sheet has 10/10/11/8 cells across its four bands.
BANDS=[
(0,242,[round(i*1536/10) for i in range(11)],0,10),
(273,512,[round(i*1536/10) for i in range(11)],10,20),
(515,754,[round(i*1536/11) for i in range(12)],20,31),
(758,993,[0,151,307,469,658,845,1025,1277,1536],31,39),
]
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("source",type=Path)
 ap.add_argument("--out",type=Path,default=Path("alina"))
 args=ap.parse_args()
 im=Image.open(args.source).convert("RGB")
 if im.size!=(1536,1024):raise SystemExit(f"Expected 1536x1024, got {im.size}")
 folder=args.out/"frames";folder.mkdir(parents=True,exist_ok=True)
 frames=[]
 for y0,y1,edges,start,end in BANDS:
  for idx in range(start,end):
   x0,x1=edges[idx-start:idx-start+2]
   # avoid neighboring cell border; keep a few pixels margin
   crop=im.crop((x0+2,y0+2,x1-2,y1-2))
   name=f"{idx+1:02d}_{LABELS[idx]}.webp"
   crop.save(folder/name,"WEBP",quality=88,method=6)
   frames.append({"id":idx+1,"state":LABELS[idx],"src":"frames/"+name})
 (args.out/"manifest.json").write_text(json.dumps({"character":"alina","source":"generated contact sheet","frames":frames},ensure_ascii=False,indent=2),encoding="utf-8")
 (args.out/"README.md").write_text("# ALINA avatar frames\n\n39 cropped WEBP frames. These are independent still images, **not** a lip-synced video or rig. The original sheet has varying framing and backgrounds; smooth animation requires aligned frames or a dedicated avatar renderer.\n\nUse manifest.json to map states. For commercial use, validate visual continuity and inspect each crop.\n",encoding="utf-8")
 print("Exported",len(frames),"frames to",args.out)
if __name__=="__main__":main()
