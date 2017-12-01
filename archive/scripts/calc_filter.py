from feature_extractor import FeatureExtractor
from obspy import read
import numpy as np
import time
from obspy.core import UTCDateTime
import os
import sys
import datetime

data_folder = '9day-aftershock/'
ts_folder = data_folder + 'timestamps/'
Fs = 100
minfreq	= 2.0
maxfreq	= 20.0
spec_length = 6.0
spec_lag	= 0.2
fp_length   = 128
fp_lag	  = 10
min_fp_length = fp_length * spec_lag + spec_length
partition_len = datetime.timedelta(hours=8)
nfreq = 32
ntimes = 64

def min_max_normalize(data):
	min_ts = min(data)
	max_ts = max(data)
	normalized = []
	for d in data:
		normalized.append((d - min_ts) / (max_ts - min_ts))
	return normalized

def get_filter(idx, ts):
	segment = st.slice(UTCDateTime(ts) - 15, UTCDateTime(ts) + 15)
	data = min_max_normalize(segment[0].data)
	result = filter(data)
	print idx, ts, result
	return result

def filter(x):
		"""
		Calculate and return sample entropy of x.
		References:
		----------
		[1] http://en.wikipedia.org/wiki/Sample_Entropy
		[2] https://www.ncbi.nlm.nih.gov/pubmed/10843903?dopt=Abstract

		:param x: the time series to calculate the feature of
		:type x: pandas.Series
		:param tolerance: normalization factor; equivalent to the common practice of expressing the tolerance as r times the standard deviation
		:type tolerance: float
		:return: the value of this feature
		:return type: float
		"""
		x = np.array(x)

		sample_length = 1 # number of sequential points of the time series
		tolerance = 0.2 * np.std(x) # 0.2 is a common value for r - why?

		n = len(x)
		prev = np.zeros(n)
		curr = np.zeros(n)
		A = np.zeros((1, 1))  # number of matches for m = [1,...,template_length - 1]
		B = np.zeros((1, 1))  # number of matches for m = [1,...,template_length]

		for i in range(n - 1):
			nj = n - i - 1
			ts1 = x[i]
			for jj in range(nj):
				j = jj + i + 1
				if abs(x[j] - ts1) < tolerance:  # distance between two vectors
					curr[jj] = prev[jj] + 1
					temp_ts_length = min(sample_length, curr[jj])
					for m in range(int(temp_ts_length)):
						A[m] += 1
						if j < n - 1:
							B[m] += 1
				else:
					curr[jj] = 0
			for j in range(nj):
				prev[j] = curr[j]

		N = n * (n - 1) / 2
		B = np.vstack(([N], B[0]))

		# sample entropy = -1 * (log (A/B))
		similarity_ratio = A / B 
		se = -1 * np.log(similarity_ratio)
		se = np.reshape(se, -1)
		return (1 if se[0] < 2.07 else 0)

if __name__ == '__main__':
	fname = sys.argv[1]
	st = read('%s%s' %(data_folder, fname))
	st.decimate(5)
	filter_file = open('new-filter.txt', 'w')
	ts_file = open(ts_folder + "ts_" + fname[:-6], "r")

	last_filter = None
	lines = ts_file.readlines()
	l = len(lines)
	i = 0
	interval = 7
	while i < l:
		ts = datetime.datetime.strptime(lines[i][:-1], "%y-%m-%dT%H:%M:%S.%f")
		if last_filter is None:
			last_filter = get_filter(i, ts)
			filter_file.write('%d\n' % last_filter)
			i += 1
		else:
			if i + interval < l:
				ts = datetime.datetime.strptime(lines[i + interval][:-1], "%y-%m-%dT%H:%M:%S.%f")
				result = get_filter(i + interval, ts)
				while result == last_filter and i + interval < l:
					for j in range(interval):
						filter_file.write('%d\n' % result)
					i += interval
					ts = datetime.datetime.strptime(lines[i + interval][:-1], "%y-%m-%dT%H:%M:%S.%f")
					result = get_filter(i + interval, ts)

			ts = datetime.datetime.strptime(lines[i][:-1], "%y-%m-%dT%H:%M:%S.%f")
			result = get_filter(i, ts)
			while result == last_filter:
				filter_file.write('%d\n' % result)
				i += 1
				if i == l:
					break
				ts = datetime.datetime.strptime(lines[i + 1][:-1], "%y-%m-%dT%H:%M:%S.%f")
				result = get_filter(i + 1, ts)


	ts_file.close()
	filter_file.close()
