from sklearn.utils import resample
import pandas as pd
import os
import numpy as np
import sys
# We want to work in ../data/<label>_bootstrapping
# - Create folder called data/<label>_bootstrapping
# - In folder, create 1000 folders, each one called data/CAR_bootstrapping/trial_#
# - In those folders, create test set. Test set will be resampled from data/010918_CAR/valid
# - Save list of folders


def sample_test_data(filenum):
	output_dir = '../data/over75_bootstrapping/'
	if not os.path.exists(output_dir):
		os.mkdir(output_dir)

	# Read files from original data folder
	original_dir = '../data/over_75/deploy/'

	files = os.listdir(original_dir)
	files = [file[:11] for file in files if file[-3:] == 'txt']

	print(filenum)
	# get random sample of files with replacementcd ..cd 
	test_files = resample(files)
	assert len(test_files) == len(files)
	os.mkdir(output_dir + '/trial_' + filenum)
	test_dir = output_dir + '/trial_' + filenum + '/deploy/'
	os.mkdir(test_dir)
	# Copy these files into test_dir

	for i, note_name in enumerate(test_files):
		note_content = open(original_dir + note_name + '.txt', 'r').readlines()
		note_file = open(test_dir + note_name +  '_' + filenum + '.txt', 'w').writelines([l for l in note_content])

		ann_content = open(original_dir + note_name + '.ann', 'r').readlines()
		ann_file = open(test_dir + note_name +  '_' + filenum + '.ann', 'w').writelines([l for l in ann_content])


if __name__ == '__main__':
	sample_test_data(sys.argv[1])