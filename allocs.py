import sys, ast, re


blocks = [0x100, 0x300, 0x600, 0x1000, 0x3000, 0x4000, 0x6000, 0x8000]

def is_alloc(line):
    return re.match(".*OsePoolAlloc.*allocate", line)
def extract(line):
    match = re.search("FSP-([0-9]+).*allocate: [^ ]* ([0-9]+)", line)
    proc = int(match.group(1))
    size = int(match.group(2))
    if re.match(".*OsePoolAlloc.*deallocate", line):
        return (proc, -size)
    return (proc, size)
allocs = [extract(line) for line in open(sys.argv[1]).read().split("\n") if is_alloc(line)]
allocs_per_proc = {}
for (proc, size) in allocs:
    if proc not in allocs_per_proc:
        allocs_per_proc[proc] = []
    allocs_per_proc[proc].append(size)

def smallest(size):
    if (size < 0):
        return -smallest(-size)
    return [block for block in blocks if block >= size][0]

for key in allocs_per_proc.keys():
    max_alloc = 0
    total = 0;
    waste = 0
    max_waste = 0
    for alloc in allocs_per_proc[key]:
        current = smallest(alloc)
        total += current
        waste += (current - alloc)
        #print alloc, current, total, waste
        max_alloc = max(total, max_alloc)
        max_waste = max(waste, max_waste)
    print max_alloc, float(max_waste) / max_alloc, [hex(a) for a in allocs_per_proc[key]]
    
    

