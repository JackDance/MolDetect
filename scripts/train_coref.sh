#!/bin/bash

NUM_NODES=1
NUM_GPUS_PER_NODE=1

BATCH_SIZE=8
ACCUM_STEP=2

PIX2SEQ_CKPT=./output/1e-4_300epoch_coco/checkpoints/best.ckpt
SAVE_PATH=output/experiment_coref_1e-4_200ep

set -x
mkdir -p $SAVE_PATH
NCCL_P2P_DISABLE=1 python main.py \
    --data_path data/coref/splits/annotations \
    --image_path data/detect/images \
    --save_path $SAVE_PATH \
    --train_file full_coref_train_filterd.json\
    --valid_file full_coref_val_filtered.json\
    --test_file full_coref_test_filtered.json\
    --format bbox \
    --input_size 1333 \
    --pix2seq \
    --split_heuristic \
    --pred_eos \
    --augment \
    --composite_augment \
    --use_hf_transformer \
    --lr 1e-4 \
    --epochs 200 --eval_per_epoch 10 \
    --warmup 0.02 \
    --label_smoothing 0. \
    --batch_size $((BATCH_SIZE / NUM_GPUS_PER_NODE / ACCUM_STEP)) \
    --gradient_accumulation_steps ${ACCUM_STEP} \
    --do_test \
    --gpus $NUM_GPUS_PER_NODE \
    --pix2seq_ckpt ${PIX2SEQ_CKPT}\


