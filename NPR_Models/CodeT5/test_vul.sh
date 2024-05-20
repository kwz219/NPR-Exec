
lr=2e-5
batch_size=2 # don't change this value, because this is a set
beam_size=50
max_source_length=512
max_target_length=256



output_dir=/SS970evo/datasets/VulRepair_dataset/result_CodeT5/mark_vr/model_set1
input_dir=/SS970evo/datasets/VulRepair_dataset/preprocess/mark_vr
checkpoint_model_type=last # best-bleu/ppl/  last
log_file=test_$checkpoint_model_type.log
load_model_path=$output_dir/checkpoint-$checkpoint_model_type/pytorch_model.bin # load checkpoint for eval
res_dir=$output_dir
summary_dir=$output_dir/summary_data
test_file=$input_dir/src-test.txt,$input_dir/tgt-test.txt
model_name_or_path=Salesforce/codet5-base
tokenizer_name=Salesforce/codet5-base
cache_path=$output_dir/cache_data
data_dir=$input_dir


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