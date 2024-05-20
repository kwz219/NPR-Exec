
lr=5e-5
batch_size=1 #64
beam_size=300
source_length=512
target_length=256
output_dir=/home/debugeval/NPR4J/results/UniXcoder
dev_file=None
test_file=/home/debugeval/NPR4J/data/dbq_onehunk_bug_loc_statistics.json
checkpoint_type=best-ppl # best-ppl/bleu last
load_model_path=/home/debugeval/NPR4J/models/Unixcoder_trained/checkpoint-best-ppl/pytorch_model.bin # checkpoint-best-bleu
log_file=dbq_onehunk_bug_loc_statistics.log
pretrained_model=/home/debugeval/NPR4J/models/unixcoder-base


python NPR_Models/UniXcoder/run2.py --do_test --model_name_or_path $pretrained_model --load_model_path $load_model_path --dev_dir $dev_file --test_filename $test_file --output_dir $output_dir --max_source_length $source_length --max_target_length $target_length --beam_size $beam_size --eval_batch_size $batch_size 2>&1| tee $output_dir/$log_file