import subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('logs', exist_ok=True)
jobs = [l.rstrip('\n').split('\t') for l in open(sys.argv[1])]
def run(j):
    w, m, l, d = j
    with open(f'logs/{w}__{l}.log', 'w') as f:
        r = subprocess.run([sys.executable, 'build.py', w, m, l, d], stdout=f, stderr=subprocess.STDOUT)
    return l, w, r.returncode
with ThreadPoolExecutor(int(sys.argv[2]) if len(sys.argv) > 2 else 4) as ex:
    for res in ex.map(run, jobs):
        print(*res, flush=True)
print('ALLDONE')
