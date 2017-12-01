f = open('filter.txt', 'r')
filtered = {}
for i, line in enumerate(f.readlines()):
	if '1' in line:
		filtered[i] = 1
f.close()

f = open('missed_pairs.txt', 'w')
reference = open('result_pairs.txt', 'r')
for line in reference.readlines():
	indices = line.split()
	x = int(indices[0])
	y = int(indices[1])
	if x not in filtered and y not in filtered:
		f.write(line)
reference.close()
f.close()