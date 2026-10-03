#!/usr/bin/env python3
"""Tiny bilingual retrieval gate. It is a smoke gate, not an MTEB replacement."""
import argparse,json,math,time,urllib.request

PAIRS=[
("serveur de sauvegarde pour machines virtuelles","Proxmox Backup Server stores versioned VM and container backups."),
("spectacle humoristique et écriture de blagues","A stand-up comedian writes jokes, punchlines and comic premises for a live comedy show."),
("recherche sémantique de documents","Semantic search retrieves passages by meaning rather than exact keywords."),
("température des disques durs","Hard drive temperature should be monitored under sustained storage load."),
("réseau USB4 entre deux ordinateurs","USB4 host-to-host networking can expose a high-speed point-to-point link."),
("transcription audio en français","French speech transcription converts recorded audio into searchable text."),
]
def embed(url,model,items):
    req=urllib.request.Request(url,data=json.dumps({"model":model,"input":items}).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=300) as r:return [x["embedding"] for x in json.load(r)["data"]]
def cos(a,b):
    return sum(x*y for x,y in zip(a,b))/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)))

ap=argparse.ArgumentParser()
ap.add_argument("--url",default="http://127.0.0.1:8091/v1/embeddings")
ap.add_argument("--model",default="local")
args=ap.parse_args()
queries=[q for q,_ in PAIRS]; docs=[d for _,d in PAIRS]
t=time.perf_counter(); qv=embed(args.url,args.model,queries); dv=embed(args.url,args.model,docs); elapsed=time.perf_counter()-t
correct=0
for i,q in enumerate(qv):
    scores=[cos(q,d) for d in dv]
    correct+=max(range(len(scores)),key=scores.__getitem__)==i
print(json.dumps({"pairs":len(PAIRS),"recall_at_1":correct/len(PAIRS),"elapsed_s":round(elapsed,4),"dimension":len(qv[0])},indent=2))
raise SystemExit(0 if correct==len(PAIRS) else 2)
