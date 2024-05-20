import os

model="/home/debugeval/NPR4J_Result/models/Processed_SR/save/SR_26/SR_26_step_50000.pt"
beam_size= 300
n_best= 300
src="/home/debugeval/NPR4J_Result/results/sequenceR/additional_buggy.txt"
tgt= "/home/debugeval/NPR4J_Result/results/sequenceR/additional_buggy.txt"
output= "/home/debugeval/NPR4J_Result/results/sequenceR/add_bugs.pred"
gpu= 0
batch_size= 1
batch_type= "sents"
max_length= 210

cmd = "python " + " ./onmt/bin/translate.py " + " --model " + str(model) + " --src " + str(src) + " --beam_size " + str(beam_size) + \
      " --n_best " + str(n_best) + " --output " + str(output) + " --gpu " + str(gpu) + " --batch_size " + str(batch_size) + " -clearml False" + ' -taskname ' + "notask" + \
      " --verbose --replace_unk --max_length " + str(max_length) +" --batch_type "+batch_type

os.system(cmd)