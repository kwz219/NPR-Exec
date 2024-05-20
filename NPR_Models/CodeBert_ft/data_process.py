import os

from Utils.BugCharacter import isHunkContinual
from Utils.ExtractContent import extractSingleHunkCode, readLines, readJson, writeJson


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
def readAPRexamples_single_hunk(bugs_info):
    """
    :param bugs_info: [file1:{filepath:fp,buggy_lines:[l1,l2...]}, file2, file3]
    :return:
    """
    examples=[]
    for idx,bug_id in enumerate(bugs_info.keys()):
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
                examples.append(
                    Example(
                        idx=idx,
                        source=extractSingleHunkCode(file_path,buggy_line_ids),
                        target="",
                    )
                )
    return examples

def read_one_example(bug_info):
    """
    :param EXAMPLE: bug_info:{id:[{"buggy_file_rel_path": "QuixBugs-master/java_programs/SHORTEST_PATH_LENGTH.java",
                              "buggy_line_ids": [
                                        37
                              ],
                              "file_content_path": "/home/debugeval/DebugEvalData\\QuixBugs\\shortest_path_length_java\\SpyAnnotationEngine.java.buggy"}]}
    :return:
    """

    pass

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


def writeLines(patched_file_lines,output_f):
    with open(output_f,'w',encoding='utf8')as f:
        for pf_line in patched_file_lines:
            f.write(pf_line)
        f.close()

    pass


def process2deval_format(pred_file_f,bugs_loc_f,output_dir,candidate_size=300):
    pred_lines = readLines (pred_file_f)
    bugs_locs = readJson(bugs_loc_f)
    bugnum = len(bugs_locs)
    assert bugnum*candidate_size == len(pred_lines)
    for idx,bugid in enumerate(bugs_locs.keys()):
        bug_infos = bugs_locs[bugid]

        #making dirs for saving formatted files
        if not os.path.exists(os.path.join(os.path.join(output_dir,bugid))):
            os.mkdir(os.path.join(output_dir,bugid))

        #prepare patched file and their meta information
        meta_infos=[]
        bug_info = bug_infos[0]
        file_content_path = bug_info["file_content_path"]
        buggy_lines = bug_info["buggy_line_ids"]
        file_name = bug_info["file_rel_path"].split("/")[-1].replace(".java","")
        patch_candidates = pred_lines[idx*candidate_size:(idx+1)*candidate_size]
        print(len(patch_candidates))
        for candid,cand_content in enumerate(patch_candidates):
            pure_patch = cand_content.replace("<PRED_START>","").replace("<PRED_END>","")
            patched_file_lines = patchhunk2file(file_content_path,buggy_lines,pure_patch)
            tgt_path = os.path.join(os.path.join(output_dir,bugid,file_name+"."+str(candid+1)+".patch"))
            writeLines(patched_file_lines,tgt_path)
            meta_infos.append({
                "bug_id": bugid,
                "patch_index": candid+1,
                "patch_contents":
                    [
                        {
                            "relative_file_position": bug_info["file_rel_path"],
                            "patch_content_position": tgt_path}
                    ]
            })
            #print(bugid,candid)
        writeJson(meta_infos,os.path.join(output_dir,bugid,bugid+".CodeBERT.patchinfo.json"))




