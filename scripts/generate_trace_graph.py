#!/usr/bin/env python3
import os
import json
import yaml

p = os.path.abspath('backend/agent/causal_rules.yaml')
with open(p,'r') as f:
    cfg = yaml.safe_load(f)

relationships = cfg.get('relationships', [])
faqs = cfg.get('faqs', [])

nodes = {}
for nid, entry in (cfg.get('intents',{}) or {}).items():
    nodes[nid] = {'id':nid,'label':entry.get('label',nid),'type':'Intent','description':entry.get('description','')}
for faq in faqs:
    fid = faq.get('id')
    nodes[fid] = {'id':fid,'label':faq.get('label',fid),'type':'FAQ','description':faq.get('action','')}
for nid, entry in (cfg.get('other_nodes',{}) or {}).items():
    nodes[nid] = {'id':nid,'label':entry.get('label',nid),'type':entry.get('type','Node'),'description':entry.get('description','')}
for fid, entry in (cfg.get('fallbacks',{}) or {}).items():
    node_id = f"fallback_{fid.lower()}"
    nodes[node_id] = {'id':node_id,'label':f"{fid} Fallback",'type':'Fallback','description':'Domain fallback node'}

links = []
for rel in relationships:
    src = rel.get('source')
    tgt = rel.get('target')
    if src not in nodes:
        nodes[src] = {'id':src,'label':src,'type':'Node','description':''}
    if tgt not in nodes:
        nodes[tgt] = {'id':tgt,'label':tgt,'type':'Node','description':''}
    links.append({'source':src,'target':tgt,'label':rel.get('label','rel')})

compiled = {'nodes': list(nodes.values()), 'links': links}
out_path = os.path.abspath('trace_graph.json')
with open(out_path,'w') as f:
    json.dump(compiled, f, indent=2)
print('WROTE', out_path, 'nodes', len(compiled['nodes']), 'links', len(compiled['links']))
