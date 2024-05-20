import json
import os
import re
import sys
from subprocess import Popen, PIPE

base_path = os.path.dirname(os.path.dirname(
                            os.path.abspath(__file__)))
parent_dir = os.path.dirname(base_path)
sys.path.append(base_path)

from BugCharacter import isHunkContinual, find_buggymethod_java
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






def prepare_buggy_func_CR3(file_path,md_start_line,md_end_line,buggy_lines):
    class_lines=readLines(file_path)
    buggy_method = class_lines[md_start_line:md_end_line+1]
    #print(buggy_method)
    pure_method = ""
    #print(buggy_lines)
    if len(buggy_lines)==1:
        buggy_method[buggy_lines[0]-md_start_line-1]= " <BUGS> "+ buggy_method[buggy_lines[0]-md_start_line-1] + " <BUGE> "
    else:
        buggy_method[buggy_lines[0] - md_start_line - 1] = " <BUGS> " + buggy_method[buggy_lines[0] - md_start_line - 1]
        buggy_method[buggy_lines[-1] - md_start_line - 1] = buggy_method[buggy_lines[-1] - md_start_line - 1] + " <BUGE> "
    for line in buggy_method:
        pure_method = pure_method+re.sub('\s+',' ',line)+'\n'
    return pure_method


def readAPRexamples_single_hunk(bugs_info):
    """
    :param bugs_info: [file1:{filepath:fp,buggy_lines:[l1,l2...]}, file2, file3]
    :return:
    """
    examples=[]
    id_bug_map={}
    idx=1
    for bug_id in bugs_info.keys():
        modified_files=bugs_info[bug_id]
        if len(modified_files)>1:
            #TODO add logger for passing multi-file bugs
            continue
        else:
            bug_info = modified_files[0]
            file_path = bug_info["file_content_path"]
            buggy_line_ids = bug_info["buggy_line_ids"]
            if not isHunkContinual(buggy_line_ids):
                #TODO add logger for passing multi-hunk bugs within a file
                continue
            else:
                start_line,end_line = buggy_line_ids[0],buggy_line_ids[-1]
                method_start_line, method_end_line = find_buggymethod_java(file_path,start_line,end_line)
                if method_start_line == None:
                    continue
                code_representation = prepare_buggy_func_CR3(file_path,method_start_line,method_end_line,buggy_line_ids)
                examples.append(
                    Example(
                        idx=idx,
                        source=code_representation,
                        target="",
                    )
                )
                id_bug_map[str(idx)]=bug_id
                idx+=1
    return examples,id_bug_map

def readLines(file_path):
    lines = []
    with open(file_path,'r',encoding='utf8')as f:
        for line in f:
            lines.append(line.strip())
        f.close()
    return lines
class Example(object):
    """A single training/test example."""
    def __init__(self,
                 idx,
                 source,
                 target,
                 ):
        self.idx = idx
        self.source = source
        self.target = target

def prepare_examples_dir(dir,mode="train"):
    if mode == "train":
        ids_f = os.path.join(dir,"trn.ids")
    else:
        ids_f = os.path.join(dir, "valid.ids")
    buggy_methods_dir = os.path.join(dir,"buggy_methods")
    buggy_lines_dir = os.path.join(dir, "buggy_lines")
    fix_lines_dir = os.path.join(dir, "fix_lines")
    return prepare_CR3_examples(ids_f, buggy_methods_dir, buggy_lines_dir, fix_lines_dir)

def prepare_CR3_examples(ids_f,buggy_methods_dir,buggy_lines_dir,fix_lines_dir):
    ids = readLines(ids_f)
    examples = []
    idx = 0
    for id in ids:
        buggy_line = open(os.path.join(buggy_lines_dir,id+".txt"),'r',encoding='utf8').read().strip()
        fix_line = open(os.path.join(fix_lines_dir,id+".txt"),'r',encoding='utf8').read().strip()
        buggy_method = readLines(os.path.join(buggy_methods_dir,id+".txt"))
        for ind in range(len(buggy_method)):
            if buggy_line in buggy_method[ind]:
                buggy_method[ind]=" <BUGS> "+ buggy_line + " <BUGE> "
                input = '\n'.join(buggy_method)
                input = re.sub('\s+',' ',input)
                output = re.sub('\s+',' '," <FIXS> "+fix_line.strip()+" <FIXE> ")
                examples.append( Example(
                    idx = idx,
                    source = input,
                    target = output,
                ))
                idx+=1
                print(idx,input,output)

    return examples

def process2deval_format(pred_file_f,id_map_f,bugs_loc_f,output_dir,candidate_size=300):

    id_maps = readJson(id_map_f)
    pred_lines = read_Lines(pred_file_f)
    bugs_locs = readJson(bugs_loc_f)
    print(len(id_maps),len(pred_lines))
    assert len(id_maps)*candidate_size == len(pred_lines)

    for ind in id_maps.keys():
        bugid = id_maps[ind]
        bug_preds = pred_lines[(int(ind)-1)*candidate_size:int(ind)*candidate_size]
        if not os.path.exists(os.path.join(os.path.join(output_dir,bugid))):
            os.mkdir(os.path.join(output_dir,bugid))
            # prepare patched file and their meta information
            meta_infos = []
            bug_info = bugs_locs[bugid][0]
            file_content_path = bug_info["file_content_path"]
            buggy_lines = bug_info["buggy_line_ids"]
            file_name = bug_info["file_rel_path"].split("/")[-1].replace(".java", "")
            patch_candidates = bug_preds
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
            writeJson(meta_infos, os.path.join(output_dir, bugid, bugid + ".unixcoder.patchinfo.json"))

process2deval_format("/home/zwk/NPR4J_Result/results/unixcoder/test.output",
                     "/home/zwk/NPR4J_Result/results/unixcoder/id_bug_match.json",
                     "/home/zwk/NPR4J_Result/data/2101_npr4j_onehunk_bug_loc_statistics.json",
                     "/home/zwk/NPR4J_Result/results/unixcoder/deval")