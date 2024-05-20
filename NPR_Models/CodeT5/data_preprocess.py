import json
from subprocess import Popen, PIPE

from torch.utils.data import TensorDataset
import numpy as np
import logging
import os
import random
import torch
import time
from tqdm import tqdm


import logging
import run_apr
import utils
import _utils
logger = logging.getLogger(__name__)
def patchhunk2file(file_patch,buggy_lines,patch_content):
    original_file_lines=[]
    with open(file_patch,'r',encoding='utf8')as f:
        for line in f:
            original_file_lines.append(line)
        f.close()
    if len(buggy_lines)==1:
        final_lines = original_file_lines[:buggy_lines[0]-1]+[patch_content+'\n']+original_file_lines[buggy_lines[0]:]
    else:
        start_line = buggy_lines[0]
        end_line = buggy_lines[1]
        final_lines = original_file_lines[:start_line-1]+[patch_content+'\n'] + original_file_lines[end_line:]
    return final_lines
def read_oriLines(file_path):
    lines = []
    with open(file_path,'r',encoding='utf8')as f:
        for line in f:
            lines.append(line)
        f.close()
    return lines

def read_Lines(file_path):
    lines = []
    with open(file_path,'r',encoding='utf8')as f:
        for line in f:
            lines.append(line.strip())
        f.close()
    return lines

def writeLines(lines,file):
    with open(file,'w',encoding='utf8')as f:
        for line in lines:
            f.write(line+'\n')
        f.close()

def write_oriLines(lines,file):
    with open(file,'w',encoding='utf8')as f:
        for line in lines:
            f.write(line)
        f.close()


def readJson(file_path):
    with open(file_path,'r',encoding='utf8')as f:
        result=json.load(f)
    return result

def writeJson(dic_result,output_path):
    with open(output_path,'w',encoding='utf8')as f:
        json.dump(dic_result,f,indent=4)

def jarWrapper(args:list):
    process = Popen(['java', '-jar']+args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    return stdout,stderr
def load_and_cache_gen_data(args, dir, pool, tokenizer, split_tag, mode = "train",only_src=False, is_sample=False):
    # cache the data into args.cache_path except it is sampled
    # only_src: control whether to return only source ids for bleu evaluating (dev/test)
    # return: examples (Example object), data (TensorDataset)
    data_tag = '_all' if args.data_num == -1 else '_%d' % args.data_num
    cache_fn = '{}/{}.pt'.format(args.cache_path, split_tag + ('_src' if only_src else '') + data_tag)

    examples = run_apr.prepare_examples_dir(dir,mode)

    if is_sample:
        examples = random.sample(examples, min(5000, len(examples)))
    if split_tag == 'train':
        utils.calc_stats(examples, tokenizer, is_tokenize=True)
    else:
        utils.calc_stats(examples)
    if os.path.exists(cache_fn) and not is_sample:
        logger.info("Load cache data from %s", cache_fn)
        data = torch.load(cache_fn)
    else:
        if is_sample:
            logger.info("Sample 5k data for computing bleu from %s", dir)
        else:
            logger.info("Create cache data into %s", cache_fn)
        tuple_examples = [(example, idx, tokenizer, args, split_tag) for idx, example in enumerate(examples)]
        features = pool.map(_utils.convert_examples_to_features, tqdm(tuple_examples, total=len(tuple_examples)))
        all_source_ids = torch.tensor([f.source_ids for f in features], dtype=torch.long)
        if split_tag == 'test' or only_src:
            data = TensorDataset(all_source_ids)
        else:
            all_target_ids = torch.tensor([f.target_ids for f in features], dtype=torch.long)
            data = TensorDataset(all_source_ids, all_target_ids)
        if args.local_rank in [-1, 0] and not is_sample:
            torch.save(data, cache_fn)
    return examples, data

def process2deval_format(pred_file_f,id_map_f,bugs_loc_f,output_dir,candidate_size=300):

    id_maps = readJson(id_map_f)
    pred_lines = read_Lines(pred_file_f)
    bugs_locs = readJson(bugs_loc_f)
    print(len(id_maps),len(pred_lines))


    for ind in id_maps.keys():
        bugid = id_maps[ind]
        bug_preds = pred_lines[(int(ind)-1)]
        if not os.path.exists(os.path.join(os.path.join(output_dir,bugid))):
            os.mkdir(os.path.join(output_dir,bugid))
            # prepare patched file and their meta information
            meta_infos = []
            bug_info = bugs_locs[bugid][0]
            file_content_path = bug_info["file_content_path"]
            buggy_lines = bug_info["buggy_line_ids"]
            file_name = bug_info["file_rel_path"].split("/")[-1].replace(".java", "")
            patch_candidates = eval(bug_preds)
            print(len(patch_candidates))

            for candid, cand_content in enumerate(patch_candidates):
                pure_patch = cand_content.replace("<FIXS>","").replace("<FIXE>","")

                patched_file_lines = patchhunk2file(file_content_path, buggy_lines, pure_patch)
                tgt_path = os.path.join(os.path.join(output_dir, bugid, file_name + "." + str(candid + 1) + ".patch"))
                write_oriLines(patched_file_lines, tgt_path)
                meta_infos.append({
                    "bug_id": bugid,
                    "patch_index": candid + 1,
                    "patch_contents":
                        [
                            {
                                "relative_file_position": bug_info["file_rel_path"],
                                "patch_content_position": tgt_path
                            }
                        ]
                })
                #print(bugid,candid)
            writeJson(meta_infos, os.path.join(output_dir, bugid, bugid + ".CodeT5.patchinfo.json"))


process2deval_format("/home/zwk/NPR4J_Result/results/codet5/test_best-ppl.output","/home/zwk/NPR4J_Result/results/codet5/id_map.json",
                     "/home/zwk/NPR4J_Result/data/2101_npr4j_onehunk_bug_loc_statistics.json","/home/zwk/NPR4J_Result/results/codet5/deval")