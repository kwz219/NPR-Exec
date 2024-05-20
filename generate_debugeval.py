import yaml

from NPR_Models.CodeBert_ft.data_process import process2deval_format
from NPR_Models.CodeBert_ft.run2 import mainWithArgs
from Utils.ExtractContent import readJson


def generate_CodeBERTft(config_file):
    with open(config_file, 'r') as f:
        config_dict = yaml.safe_load(f)
        f.close()
    eval_batch_size = config_dict["eval_batch_size"]

    model_type = config_dict["model_type"]
    model_path = config_dict["model_name_or_path"]

    load_model_path = config_dict["load_model_path"]
    beam_size = int(config_dict["beam_size"])
    pref_file = config_dict["pred_file"]
    debugeval_bugsinfo_path = config_dict["debugeval_bugsinfo_path"]
    debugeval_output_dir = config_dict["debugeval_output_dir"]
    bugs_infos = readJson(debugeval_bugsinfo_path)


    mainWithArgs(gradient_accumulation_steps=1, train_batch_size=1, train_filename='', do_train=False,
                 train_steps=0, learning_rate=0, do_eval=False, eval_steps=0, test_filename='', do_test=True,
                 warmup_steps=0, max_source_length=256, max_target_length=128, beam_size=beam_size, tokenizer_name="",
                 weight_decay=0, adam_epsilon=1e-8,
                 dev_file_name=None, eval_batch_size=eval_batch_size, config_name="", model_name_or_path=model_path,
                 model_type=model_type,
                output_dir='', load_model_path=load_model_path, bugs_info=bugs_infos, pred_file=pref_file)

    process2deval_format(pred_file_f=pref_file,bugs_loc_f=debugeval_bugsinfo_path,output_dir=debugeval_output_dir)
#generate_CodeBERTft("Configs/DebugEval/generate_CodeBERT-ft.yaml")