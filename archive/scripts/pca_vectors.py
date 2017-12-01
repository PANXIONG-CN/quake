from feature_extractor import FeatureExtractor
from obspy import read
import numpy as np
import time
from obspy.core import UTCDateTime
import os
import sys
import datetime

data_folder = '9day-aftershock/'
fp_folder = data_folder + 'fingerprints/'
ts_folder = data_folder + 'timestamps/'
if not os.path.exists(fp_folder):
	os.makedirs(fp_folder)
if not os.path.exists(ts_folder):
	os.makedirs(ts_folder)
Fs = 20
minfreq    = 2.0
maxfreq    = 20.0
spec_length = 6.0
spec_lag    = 0.2
fp_length   = 128
fp_lag      = 10
min_fp_length = fp_length * spec_lag + spec_length
partition_len = datetime.timedelta(hours=8)
nfreq = 32
ntimes = 64
feats = FeatureExtractor(sampling_rate=Fs, window_length=spec_length, window_lag=spec_lag, 
		fingerprint_length=fp_length, fingerprint_lag=fp_lag)

def write_timestamp(t, idx1, idx2, starttime, ts_file):
	fp_timestamp = np.asarray([t[int(np.mean((idx1[j], idx2[j])))] for j in range(len(idx1))])
	for ts in fp_timestamp:
		ts_file.write((starttime + datetime.timedelta(seconds = ts)).strftime('%y-%m-%dT%H:%M:%S.%f') + '\n')

def write_fp(haar_images, fp_file):
	for vec in haar_images:
		for i in range(len(vec)):
			if i < len(vec) - 1:
				fp_file.write(str(vec[i]) + ',')
			else:
				fp_file.write(str(vec[i]) + '\n')


if __name__ == '__main__':
	fname = sys.argv[1]
	st = read('%s%s' %(data_folder, fname))
	# Downsample to 20 Hz
	st.decimate(5)

	ts_file = open(ts_folder + "ts_" + fname[:-6], "a")
	fp_file = open(fp_folder + "fp_" + fname[:-6], "a")
	last_normalized = datetime.datetime.strptime(str(st[0].stats.starttime), '%Y-%m-%dT%H:%M:%S.%fZ')
	partial_haar_images = np.zeros([0, int(nfreq) * int(ntimes)])
	t00 = time.time()
	for i in range(len(st)):
		# Get start and end time of the current continuous segment
		starttime = datetime.datetime.strptime(str(st[i].stats.starttime), '%Y-%m-%dT%H:%M:%S.%fZ')
		endtime = datetime.datetime.strptime(str(st[i].stats.endtime), '%Y-%m-%dT%H:%M:%S.%fZ')
		# Ignore segments that are shorter than one spectrogram window length
		if endtime - starttime < datetime.timedelta(seconds = min_fp_length):
			continue

		# Spectrogram + Wavelet transform
		haar_images, nWindows, idx1, idx2, Sxx, t  = feats.data_to_haar_images(st[i].data)
		# Write fingerprint time stamps to file
		write_timestamp(t, idx1, idx2, starttime, ts_file)
		write_fp(haar_images, fp_file)

	ts_file.close()
	fp_file.close()
	t000 = time.time()
	print("Normalized real value fingerprints took: %.2f seconds" % (t000 - t00))
