import csv, pandas as pd, tomllib
W='weeks/2026-w10/'; T='data/2026-w10/FanDuel-NFL-2026-11-15-136490-entries-upload-template.csv'
OUT=W+'edit_entries_149.csv'
rd=lambda p:[l.split(',') for l in open(p,encoding='utf-8').read().splitlines()[1:]]
old=[r[:9] for r in rd(W+'entered_as_uploaded/entered_upload_149.csv')]
new_all=[r[:9] for r in rd(W+'upload.csv')]
r=pd.read_csv(W+'readable.csv'); drop=int(r.Proj.idxmin()); print('new set: drop lineup',drop+1,r.Proj[drop])
keep=[i for i in range(150) if i!=drop]; new=[new_all[i] for i in keep]
rows=list(csv.reader(open(T,newline='',encoding='utf-8-sig')))
cols=list(range(4,13)); assert rows[0][4:13]==['QB','RB','RB','WR','WR','WR','TE','FLEX','DEF'], rows[0]
oldsets={frozenset(o):k for k,o in enumerate(old)}
entries=[i for i in range(1,len(rows)) if rows[i] and rows[i][0].isdigit()]
used=set(); plan={}; other=[]
for i in entries:
    k=oldsets.get(frozenset(rows[i][4:13]))
    if k is None or k in used: other.append(i); continue
    used.add(k); plan[i]=k
print('entries',len(entries),'matched uploaded',len(plan),'left unchanged',[(rows[i][0],rows[i][4:13]) for i in other])
assert len(plan)==149
for n,(i,k) in enumerate(sorted(plan.items())):
    rows[i][4:13]=new[n]
with open(OUT,'w',newline='',encoding='utf-8') as f: csv.writer(f,quoting=csv.QUOTE_ALL).writerows(rows)
pd.DataFrame([r.iloc[i] for i in keep]).to_csv(W+'rebuild_readable_149.csv',index=False)
# ---- validate the written file
s=pd.read_csv('data/2026-w10/fd_players.csv',keep_default_na=False).set_index('Id')
cfg=tomllib.load(open('config/2026-w10/week.toml','rb'))
bad=set(cfg['status']['out'])|set(cfg['status']['questionable'])|set(cfg['prefs']['red'])
back=list(csv.reader(open(OUT,newline='',encoding='utf-8')))
tmpl=list(csv.reader(open(T,newline='',encoding='utf-8-sig')))
assert back[0]==tmpl[0] and len(back)==len(tmpl)
slots=['QB','RB','RB','WR','WR','WR','TE',None,'D']; err=[]; seen=set(); cnt={}; changed=0
for i in range(1,len(back)):
    if [c for j,c in enumerate(back[i]) if j not in cols]!=[c for j,c in enumerate(tmpl[i]) if j not in cols]: err.append((i,'non-player col changed'))
    if i not in plan:
        if back[i]!=tmpl[i]: err.append((i,'non-entry row changed'))
        continue
    ids=back[i][4:13]; changed+=ids!=tmpl[i][4:13]
    p=s.loc[ids]
    if len(set(ids))!=9: err.append((i,'dup'))
    for k,(sl,(_,pl)) in enumerate(zip(slots,p.iterrows())):
        if sl and pl.Position!=sl: err.append((i,'slot',pl.Nickname))
        if k==7 and pl.Position not in('RB','WR','TE'): err.append((i,'flex'))
        if pl['Injury Indicator']!='': err.append((i,'tag',pl.Nickname))
        if pl.Nickname in bad: err.append((i,'bad',pl.Nickname))
        cnt[pl.Nickname]=cnt.get(pl.Nickname,0)+1
    if not 59000<=p.Salary.sum()<=60000: err.append((i,'salary',p.Salary.sum()))
    if max(p.Team.value_counts())>4: err.append((i,'team>4'))
    if (p.iloc[:8].Team==p.iloc[8].Opponent).any(): err.append((i,'vs DST'))
    qb=p.iloc[0]
    if (p.iloc[1:8].Team==qb.Team).sum()<2 or (p.iloc[1:8].Team==qb.Opponent).sum()<1: err.append((i,'stack'))
    key=frozenset(ids)
    if key in seen: err.append((i,'dup lineup'))
    seen.add(key)
print('ERRORS',len(err),err[:10]); print('entries changed',changed,'of 149')
print('Etienne',cnt.get('Travis Etienne Jr.',0),'Emmett Johnson',cnt.get('Emmett Johnson',0),'Lock',cnt.get('Drew Lock',0),'Cousins',cnt.get('Kirk Cousins',0),'Lloyd',cnt.get('MarShawn Lloyd',0))
print('top',sorted(cnt.items(),key=lambda x:-x[1])[:8]); print('mean proj',round(r.iloc[keep].Proj.mean(),1))
