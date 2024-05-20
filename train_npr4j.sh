
lr=5e-5 # 5e-5
batch_size=8 # 8/16/32/64
beam_size=5
source_length=512
target_length=128
output_dir=/home/debugeval/NPR4J/models/Unixcoder_trained
input_dir=/dataset/SequenceR_dataset/preprocess/mark2_src
train_dir=/home/debugeval/NPR4J/data/Train_Data/Train
dev_dir=/home/debugeval/NPR4J/data/Train_Data/Valid
log_file=train_set1.log
epochs=30  # 30
pretrained_model=/home/debugeval/NPR4J/models/unixcoder-base

mkdir -p $output_dir

python NPR_Models/UniXcoder/run2.py --do_train --do_eval --model_name_or_path $pretrained_model --train_dir $train_dir --dev_dir $dev_dir --output_dir $output_dir --max_source_length $source_length --max_target_length $target_length --beam_size $beam_size --train_batch_size $batch_size --eval_batch_size $batch_size --learning_rate $lr --num_train_epochs $epochs 2>&1| tee $output_dir/$log_file


	