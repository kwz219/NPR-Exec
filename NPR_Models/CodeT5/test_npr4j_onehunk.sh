
lr=5e-5
batch_size=2 # don't change this value, because this is a set
beam_size=50
max_source_length=512
max_target_length=128



output_dir=/home/debugeval/NPR4J/results/CodeT5
input_dir=/SS970evo/datasets/SequenceR_dataset/preprocess/mark2_src
checkpoint_model_type=best-ppl # best-bleu/ppl/  last
log_file=test_$checkpoint_model_type.log
load_model_path=/home/debugeval/NPR4J/models/codet5_trained/checkpoint-best-ppl/pytorch_model.bin # load checkpoint for eval
res_dir=$output_dir
summary_dir=$output_dir/summary_data
test_file=/home/debugeval/NPR4J/data/dbq_onehunk_bug_loc_statistics.json
model_name_or_path=/home/debugeval/NPR4J/models/codet5-base
tokenizer_name=/home/debugeval/NPR4J/models/codet5-base
cache_path=$output_dir/cache_data
data_dir=None


python ./run_apr_sequencer.py \
--do_test \
--model_type codet5 \
--model_name_or_path $model_name_or_path \
--checkpoint_model_type $checkpoint_model_type \
--tokenizer_name $tokenizer_name \
--test_filename $test_file \
--output_dir $output_dir \
--max_source_length $max_source_length \
--max_target_length $max_target_length \
--load_model_path $load_model_path \
--beam_size $beam_size \
--learning_rate $lr \
--eval_batch_size $batch_size \
--cache_path $cache_path \
--summary_dir $summary_dir \
--data_dir $data_dir \
--res_dir $res_dir \
--task refine \
--learning_rate $lr \
2>&1| tee $output_dir/$log_file