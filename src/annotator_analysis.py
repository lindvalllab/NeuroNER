import re
import pandas as pd
import os
import spacy
import difflib
import numpy as np
import csv
import pickle
import itertools
import ast
from collections import Counter, defaultdict
from sklearn.metrics import cohen_kappa_score, confusion_matrix, precision_recall_fscore_support, classification_report
from pycci_preprocessing import clean_df


def parse_ann_column(row, op):
	val = row[op]
	if op + '_2' not in row:
		if type(val) == float:
			if np.isnan(val):
				return 'O'
		else:
			if val == 'O':
				return 'O'
			return ast.literal_eval(val)

	val2 = row[op + '_2']

	if type(val) == float:
		if np.isnan(val):
			val = 'O'
	if type(val2) == float:
		if np.isnan(val2):
			val2 = 'O'

	if val == 'O' and val2 == 'O':
		return 'O'
	elif val == 'O':
		return ast.literal_eval(val2)
	elif val2 == 'O':
		return ast.literal_eval(val)
	else:
		total = list(set(ast.literal_eval(val)+ast.literal_eval(val2)))
		return total

def get_annotator_headers(annotators):
	total = annotators[:]
	for ann in annotators:
		total.append(ann + '_2')
	return total

def shorten_raw_annotations(annotators, annotations_file, out_filename):
	subset = get_annotator_headers(annotators)
	ann_df = pd.read_csv(annotations_file, index_col=0, header=0, dtype=object)
	mask = (ann_df[subset].isin(['O']) | ann_df[subset].isnull()).all(axis=1)
	ann_df = ann_df[~mask]
	ann_df.to_csv(out_filename)

def get_unreviewed_notes(raw_annotations_file, notes_file, out_filename, text_columns, keep_columns):
	ann_df = clean_df(pd.read_csv(raw_annotations_file, index_col=0, header=0), text_columns)
	notes_df = pd.read_csv(notes_file, header=0, index_col=0)
	annotators = ann_df['operator'].unique().tolist()
	ann_dict = get_notes_by_annotator(ann_df, annotators)
	# Invert dictionary
	reversed_dict = defaultdict(list)
	for ann,row_ids in ann_dict.items():
		# Maps row_id to annotators
		for row_id in row_ids:
			reversed_dict[row_id].append(ann)

	single_note_list = [note for note, annotators in reversed_dict.items() if len(annotators) == 1]
	save_df = notes_df[notes_df['ROW_ID'].isin(single_note_list)]
	# Add annotators
	save_df['operator'] = save_df.apply(lambda row: reversed_dict[row['ROW_ID']], axis=1).tolist()
	save_df = save_df[keep_columns]
	save_df.to_csv(out_filename)

def get_notes_by_annotator(annotations_df, annotators):
	results_dict = {}
	for annotator in annotators:
		op_df = annotations_df[annotations_df['operator'] == annotator]
		row_ids = list(map(int, map(float, op_df['ROW_ID'].unique())))
		results_dict[annotator] = row_ids
	return results_dict

def _get_annotator_headers(annotators):
	header = annotators[:]
	for ann in header:
		header.append(ann + '_2')
	return header

def calc_kappa(token_annotations_file, annotators, labels, out_filename):
	ann_df = pd.read_csv(token_annotations_file, index_col=0, header=0, dtype=object)
	op_combinations = list(itertools.combinations(annotators, 2))
	results_list = []
	results_headers = ['op1', 'op2', 'num_overlap', 'label', 'kappa', 'op1_count', 'op2_count']
	for op, op2 in op_combinations:
		row_ids = ann_df.dropna(subset=[op])['note_name'].unique().tolist()
		row_ids2 = ann_df.dropna(subset=[op2])['note_name'].unique().tolist()

		# Find overlap in row_ids
		intersect_ids = set(map(str, set(row_ids).intersection(row_ids2)))
		if len(intersect_ids) == 0:
			continue
		num_overlap = len(intersect_ids)
		print(op, op2, num_overlap)

		# Get annotations from both operators per token
		intersect_df = ann_df[ann_df['note_name'].isin(intersect_ids)]

		# If operator annotated twice, then take the aggregate of the annotations
		y = intersect_df.apply(lambda row: parse_ann_column(row, op), axis=1).tolist()
		y2 = intersect_df.apply(lambda row: parse_ann_column(row, op2), axis=1).tolist()

		assert len(y) == len(y2)

		# Retrieve annotations by label
		for label in labels:
			print(label)
			y_label = [label if label in val else 'O' for val in y]
			y2_label = [label if label in val else 'O' for val in y2]
			kappa = cohen_kappa_score(y_label, y2_label)
			results_list.append({
				'op1': op,
				'op2': op2,
				'num_overlap': num_overlap,
				'label': label, 
				'kappa': kappa,
				'op1_count': y_label.count(label),
				'op2_count': y2_label.count(label)})
			print(kappa)

	results_df = pd.DataFrame(results_list)
	results_df = results_df[results_headers]
	results_df.to_csv(out_filename)

def calc_kappa_note_level(note_labels_file, annotators, labels, out_filename):
	ann_df = pd.read_csv(note_labels_file, index_col=0, header=0, dtype=object)
	op_combinations = list(itertools.combinations(annotators, 2))
	results_list = []
	results_headers = ['true/y1', 'pred/y2', 'num_overlap', 'label', 'kappa', 'precision', 'recall', 'specificity', 'f1', 'op1_count', 'op2_count']
	for op, op2 in op_combinations:
		row_ids = ann_df.dropna(subset=[op])['note_name'].unique().tolist()
		row_ids2 = ann_df.dropna(subset=[op2])['note_name'].unique().tolist()

		# Find overlap in row_ids
		intersect_ids = set(map(str, set(row_ids).intersection(row_ids2)))
		if len(intersect_ids) == 0:
			continue
		num_overlap = len(intersect_ids)

		# Get annotations from both operators per token
		intersect_df = ann_df[ann_df['note_name'].isin(intersect_ids)]
		# If operator annotated twice, then take the aggregate of the annotations
		y = intersect_df.apply(lambda row: parse_ann_column(row, op), axis=1).tolist()
		y2 = intersect_df.apply(lambda row: parse_ann_column(row, op2), axis=1).tolist()

		assert len(y) == len(y2)

		# Retrieve annotations by label
		for label in labels:
			if label == 'CIM':
				y_label = [label if 'CAR' in val or 'LIM' in val else 'O' for val in y]
				y2_label = [label if 'CAR' in val or 'LIM' in val else 'O' for val in y2]
			else:
				y_label = [label if label in val else 'O' for val in y]
				y2_label = [label if label in val else 'O' for val in y2]
			kappa = cohen_kappa_score(y_label, y2_label)
			report = classification_report(y_label, y2_label)
			lines = report.split('\n')
			report_data = []
			for line in lines[2:-3]:
				row = {}
				row_data = line.split()
				print(row_data)
				row['class'] = row_data[0]
				row['precision'] = float(row_data[1])
				row['recall'] = float(row_data[2])
				row['f1_score'] = float(row_data[3])
				row['support'] = float(row_data[4])
				report_data.append(row)
			report_df = pd.DataFrame.from_dict(report_data)
			print(report_df)
			results_list.append({
				'true/y1': op,
				'pred/y2': op2,
				'num_overlap': num_overlap,
				'label': label, 
				'kappa': kappa,
				'precision': report_df.iloc[0]['precision'],
				'recall': report_df.iloc[0]['recall'],
				'specificity':report_df.iloc[1]['recall'],
				'f1': report_df.iloc[0]['f1_score'],
				'op1_count': y_label.count(label),
				'op2_count': y2_label.count(label)})

	results_df = pd.DataFrame(results_list)
	results_df = results_df[results_headers]
	results_df.to_csv(out_filename)

text_columns = ["TEXT", "Patient and Family Care Preferences Text",
"Communication with Family Text",
"Full Code Status Text",
"Code Status Limitations Text",
"Palliative Care Team Involvement Text",
"Ambiguous Text",
"Ambiguous Comments"]

labels_dict = {"Patient and Family Care Preferences": 'CAR',
"Communication with Family":'FAM',
"Full Code Status": 'COD',
"Code Status Limitations": 'LIM',
"Palliative Care Team Involvement": 'PAL',
"Ambiguous": 'AMB'}


labels = ['COD', 'LIM', 'CAR', 'FAM', 'CIM']
annotators = ['gold', 'Saad', 'Sarah', 'Harry', 'Dickson']
keep_columns = ['HADM_ID', 'ROW_ID', 'CHARTDATE', 'CATEGORY', 'DESCRIPTION', 'TEXT', 'operator']

#calc_kappa('../temp/gold_data/final_merged_011918.csv', annotators, labels, '../temp/011918/kappas_011918.csv')
#calc_kappa_note_level('../temp/gold_data/annotator/note_labels_011918.csv', annotators, labels, '../temp/derp.csv')
