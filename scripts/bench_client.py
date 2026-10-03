#!/usr/bin/env python3
import argparse, concurrent.futures, json, statistics, time, urllib.request

ap=argparse.ArgumentParser()
ap.add_argument("--url",default="http://127.0.0.1:8091/v1/embeddings")
ap.add_argument("--model",default="local")
ap.add_argument("--batch",type=int,default=8)
ap.add_argument("--requests",type=int,default=8)
ap.add_argument("--concurrency",type=int,default=1)
ap.add_argument("--tokens-ish",type=int,default=256,help="approximate word-sized repetitions per input")
args=ap.parse_args()

seed="Cloud9 semantic retrieval benchmark français English multilingual local embedding. "
text=(seed*((args.tokens_ish+7)//8))[:args.tokens_ish*10]
payload=json.dumps({"model":args.model,"input":[text+str(i) for i in range(args.batch)]}).encode()

def one(_):
    req=urllib.request.Request(args.url,data=payload,headers={"Content-Type":"application/json"})
    t=time.perf_counter()
    with urllib.request.urlopen(req,timeout=300) as r:
        obj=json.load(r)
    return time.perf_counter()-t,len(obj["data"]),len(obj["data"][0]["embedding"])

# warm-up
one(0)
t=time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
    vals=list(ex.map(one,range(args.requests)))
wall=time.perf_counter()-t
lat=[v[0] for v in vals]
emb=sum(v[1] for v in vals)
print(json.dumps({
    "requests":args.requests,
    "batch":args.batch,
    "concurrency":args.concurrency,
    "wall_s":round(wall,4),
    "request_s":round(args.requests/wall,3),
    "embeddings_s":round(emb/wall,3),
    "latency_mean_s":round(statistics.mean(lat),4),
    "latency_p95_s":round(sorted(lat)[max(0,int(.95*len(lat))-1)],4),
    "dimension":vals[0][2],
},indent=2))
