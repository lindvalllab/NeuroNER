#!/bin/bash
for i in {1234..1290}; do
	echo $i
	echo "CUDA_VISIBLE_DEVICES=2 python3.5 main.py --train_model=False --use_pretrained_model=True --dataset_text_folder=../data/COD_bootstrapping/trial_$i/ --pretrained_model_folder=../trained_models/cod_model --output_folder=../output/COD_bootstrapping/trial_$i/ >> bootstrap_COD.txt"
	CUDA_VISIBLE_DEVICES=2 python3.5 main.py --train_model=False --use_pretrained_model=True --dataset_text_folder=../data/COD_bootstrapping/trial_$i/ --pretrained_model_folder=../trained_models/cod_model --output_folder=../output/COD_bootstrapping/trial_$i/ >> bootstrap_COD.txt
done