
import testone_ghl as test
model_path= "/root/autodl-tmp/npr4j_addex/Recoder_trained/best_model.ckpt"


search_size= 300
bugs_info_path = "/root/autodl-tmp/npr4j_addex/autodl_npr4j_onehunk_bug_loc_statistics.json"
output_dir= "/root/autodl-tmp/npr4j_addex/recoder_result"
valdatapkl_f= "/root/autodl-tmp/npr4j_addex/Recoder_trained/valdata.pkl"
nl_voc_f= "/root/autodl-tmp/npr4j_addex/Recoder_trained/nl_voc.pkl"
rule_f= "/root/autodl-tmp/npr4j_addex/Recoder_trained/rule.pkl"
code_voc_path= "/root/autodl-tmp/npr4j_addex/Recoder_trained/code_voc.pkl"
char_voc_path= "/root/autodl-tmp/npr4j_addex/Recoder_trained/char_voc.pkl"
rulead_path= "/root/autodl-tmp/npr4j_addex/Recoder_trained/rulead.pkl"
NL_voc_size= 26167
code_voc_size= 26167
voc_size= 81
rule_num= 1265
cnum= 764

test.generate_fixes_deval_onehunk(model_path,bugs_info_path,search_size,output_dir,valdatapkl_f,nl_voc_f,rule_f,code_voc_path,char_voc_path,rulead_path,NL_voc_size,code_voc_size,voc_size,rule_num,cnum)