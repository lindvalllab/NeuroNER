#!/bin/bash
echo 'CUDA_VISIBLE_DEVICES=2 python3.5 main.py --train_model=False --use_pretrained_model=True --dataset_text_folder=../data/$1/$4 --pretrained_model_folder=../trained_models/$2 --output_folder=../output/$1/$4/ >>  $3'