import json
import os
import re
import shutil
from subprocess import Popen, PIPE
import BugCharacter as bc
import javalang

def readJson(file_path):
    with open(file_path,'r',encoding='utf8')as f:
        result=json.load(f)
    return result
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
def writeJson(dic_result,output_path):
    with open(output_path,'w',encoding='utf8')as f:
        json.dump(dic_result,f,indent=4)

def jarWrapper(args:list):
    process = Popen(['java', '-jar']+args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    return stdout,stderr
def read_Lines(file_path):
    lines = []
    with open(file_path,'r',encoding='utf8')as f:
        for line in f:
            lines.append(line.strip())
        f.close()
    return lines
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
def preprocess_SequenceR_Buggy_deval(bug_loc_file,tmp_dir,output_prefix,jar_path):

    bug_loc_infos = readJson(bug_loc_file)
    ids = list(bug_loc_infos.keys())
    success_ids=[]
    failed_ids=[]
    abstracted_lines=[]

    def truncate(class_lines, max_length=1000):
        length_list = []
        for line in class_lines:
            try:
                toked = javalang.tokenizer.tokenize(line)
                length_list.append(len(toked))
                # toked_codes.append(' '.join([tok.value for tok in toked]))
            except:
                toked = re.split(r"[.,!?;(){}]", line)
                length_list.append(len(toked))
                # toked_codes.append(' '.join(toked))
        # print("tokenized")
        assert len(length_list) == len(class_lines)
        length_sum = sum(length_list)
        if length_sum <= max_length:
            return class_lines
        else:
            "start to delete from the end"
            cur_len_satisfy = False
            end_pos = len(class_lines)
            while end_pos > 0:
                total_length = sum(length_list[:end_pos])
                if total_length <= max_length:
                    cur_len_satisfy = True
                    break
                elif "<START_BUG>" in class_lines[end_pos - 1] or "<END_BUG>" in class_lines[end_pos - 1]:
                    break
                else:
                    end_pos = end_pos - 1
            if cur_len_satisfy:
                return class_lines[:end_pos]
            else:
                start_pos = 0
                while start_pos < end_pos:
                    total_len = sum(length_list[start_pos:end_pos])
                    if total_len <= max_length:
                        return class_lines[start_pos:end_pos]
                    elif "<START_BUG>" in class_lines[start_pos] or "<END_BUG>" in class_lines[
                        start_pos]:
                        break
                    else:
                        start_pos += 1
                return class_lines[start_pos:end_pos]
    for id in ids:
        print(id)
        print("=============",len(abstracted_lines))


        # e.g. of id: project_filename_faultyline
        bug_info = bug_loc_infos[id]
        buggy_file_info = bug_info[0]
        err_lines = buggy_file_info["buggy_line_ids"]
        err_start = err_lines[0]
        err_end = err_lines[-1]

        buggy_file_path = buggy_file_info["file_content_path"]

        print("error line ids", err_start, err_end)


        #print("error line ids",err_start,err_end)
        "generate abstract file of buggy class"
        file_name = buggy_file_path.split("/")[-1].replace(".java.buggy", "")
        shutil.copyfile(buggy_file_path, buggy_file_path.replace(".buggy", ""))
        buggy_class_f = buggy_file_path.replace(".buggy", "")
        output_f = tmp_dir + '/' + file_name + '.java'
        args = [jar_path, buggy_class_f, output_f]
        if not os.path.exists(output_f):
            out, err = jarWrapper(args)
            print(out,err)

        "add error label to the method"
        m_start_line, m_end_line = bc.find_buggymethod_java(buggy_class_f, err_start, err_end)
        class_lines = read_Lines(buggy_class_f)
        skipflag =False
        if m_start_line == None:
            skipflag = True
            if err_start == err_end:
                class_lines[err_start - 1] = "<START_BUG> "+ class_lines[err_start-1].rstrip() + " <END_BUG>"
            else:
                class_lines[err_start - 1] = "<START_BUG> "+ class_lines[err_start-1]
                class_lines[err_end - 1] = class_lines[err_start-1].rstrip() + " <END_BUG>"
            abstract_class = truncate(class_lines, 300)
            try:
                toked_bug = javalang.tokenizer.tokenize(' '.join(abstract_class))
                toked_bug = ' '.join([tok.value for tok in toked_bug]).replace('< START_BUG >',
                                                                           '<START_BUG>').replace('< END_BUG >',
                                                                                                  '<END_BUG>')
                success_ids.append(id)
                abstracted_lines.append(toked_bug.strip().replace('\r\n', ' ').replace('\n', ' '))
            except:
                toked_bug = re.split(r"([.,!?;(){}])", ' '.join(abstract_class))
                toked_bug = ' '.join(toked_bug).replace('< START_BUG >', '<START_BUG>').replace('< END_BUG >',
                                                                                                '<END_BUG>')
                if not ("<START_BUG>" in toked_bug and "<END_BUG>" in toked_bug):
                    exit(1)
                    failed_ids.append(id)
                    print("fail",id)
                else:
                    success_ids.append(id)
                    abstracted_lines.append(toked_bug.strip().replace('\r\n',' ').replace('\n',' '))
        if skipflag:
            continue
        method_lines = class_lines[m_start_line:m_end_line + 1]
        rel_err_start = err_start - m_start_line - 1
        rel_err_end = err_end - m_start_line - 1
        if err_start == err_end:

            method_lines[rel_err_start]= " <START_BUG> "+ method_lines[rel_err_start] +" <END_BUG> "
            buggy_line = method_lines[rel_err_start]
        else:
            method_lines[rel_err_start] = " <START_BUG> "+ method_lines[rel_err_start]
            method_lines[rel_err_end] = method_lines[rel_err_end].rstrip()+" <END_BUG> "
            buggy_line = ' '.join(method_lines[rel_err_start:rel_err_end+1])



        print("buggy_line",buggy_line)
        success_ids.append(id)
        abstracted_lines.append(' '.join(method_lines).replace('\r\n',' ').replace('\n',' '))
        continue

        "generate 3-level abstract file"
        abstract_class=[]
        success_flag=0
        error_start_in_class=err_start-1
        error_end_in_class = err_end-1
        try:
            class_lines = read_Lines(output_f)
            for idx,line in enumerate(class_lines):

                check_line = buggy_line.replace("<START_BUG>","").replace("<END_BUG>","")

                if check_line.strip() in line.strip():
                    print(idx)
                    abstract_class = class_lines[:idx]+method_lines+class_lines[idx+1:]
                    success_flag=1
                    error_start_in_class = idx+error_start_in_class
                    error_end_in_class = idx+error_end_in_class
                    break

            #print(len(abstract_class))
            clean_class=[]
            ori_error_start_in_class = error_start_in_class
            ori_error_end_in_class = error_end_in_class
            #print(abstract_class)
            #print("error position in class:",error_start_in_class,error_end_in_class)
            #print("buggy line in class:",abstract_class[error_start_in_class].strip(),abstract_class[error_end_in_class].strip())

            for idx,line in enumerate(abstract_class):
                line4check=str(line.strip())
                if line4check.startswith("/") or line4check.startswith("*") or line4check=="" or line4check==r"*/":
                    if idx<ori_error_start_in_class:
                        error_start_in_class= error_start_in_class-1
                        error_end_in_class = error_end_in_class-1
                    elif idx >= ori_error_start_in_class and idx<=ori_error_end_in_class:
                        clean_class.append(line)
                else:
                    #print(line.strip())
                    clean_class.append(line)

            #print(clean_class)
            #print(error_start_in_class,error_end_in_class)
            #print("error_line_inclean: ",clean_class[error_start_in_class].strip(),clean_class[error_end_in_class].strip())
            assert clean_class[error_start_in_class].strip()==method_lines[err_start].strip()
            assert clean_class[error_end_in_class].strip() == method_lines[err_end].strip()
            if success_flag ==1:

                def count_length(lines):
                    length_list=[]
                    for line in lines:
                        length_list.append(len(re.split(r"[.,!?;(){}]", line)))
                    return sum(length_list)
                if count_length(clean_class)>=1000:
                    abstract_class=method_lines
                else:
                    abstract_class=clean_class
                #print("<START_BUG>" in ' '.join(abstract_class), "<END_BUG>" in ' '.join(abstract_class))
            else:
                abstract_class=method_lines

            "tokenize source codes"
            print("before", count_length(abstract_class))
            abstract_class=truncate(abstract_class,300)
            print("after",count_length(abstract_class))
            try:
                toked_bug = javalang.tokenizer.tokenize(' '.join(abstract_class))
                toked_bug = ' '.join([tok.value for tok in toked_bug]).replace('< START_BUG >',
                                                                           '<START_BUG>').replace('< END_BUG >',
                                                                                                  '<END_BUG>')
            except:
                toked_bug = re.split(r"([.,!?;(){}])", ' '.join(abstract_class))
                toked_bug = ' '.join(toked_bug).replace('< START_BUG >', '<START_BUG>').replace('< END_BUG >',
                                                                                                '<END_BUG>')


            if not ("<START_BUG>" in toked_bug and "<END_BUG>" in toked_bug):
                exit(0)
                try:
                    toked_bug = javalang.tokenizer.tokenize(' '.join(abstract_class))
                    toked_bug = ' '.join([tok.value for tok in toked_bug]).replace('< START_BUG >',
                                                                                   '<START_BUG>').replace('< END_BUG >',
                                                                                                          '<END_BUG>')
                    success_ids.append(id)
                    abstracted_lines.append(toked_bug.strip().replace('\r\n', ' ').replace('\n', ' '))
                except:
                    toked_bug = re.split(r"([.,!?;(){}])", ' '.join(abstract_class))
                    toked_bug = ' '.join(toked_bug).replace('< START_BUG >', '<START_BUG>').replace('< END_BUG >',
                                                                                                    '<END_BUG>')
                    if not ("<START_BUG>" in toked_bug and "<END_BUG>" in toked_bug):
                        print(id)
                        failed_ids.append(id)
                    else:
                        success_ids.append(id)
                        abstracted_lines.append(toked_bug.strip().replace('\r\n',' ').replace('\n',' '))
            else:
                success_ids.append(id)
                print("added",len(toked_bug.split()))
                abstracted_lines.append(toked_bug.strip().replace('\r\n',' ').replace('\n',' '))

        except:
            abstract_class = truncate(abstract_class, 300)
            try:
                toked_bug = javalang.tokenizer.tokenize(' '.join(abstract_class))
                toked_bug = ' '.join([tok.value for tok in toked_bug]).replace('< START_BUG >',
                                                                           '<START_BUG>').replace('< END_BUG >',
                                                                                                  '<END_BUG>')
                success_ids.append(id)
                abstracted_lines.append(toked_bug.strip().replace('\r\n', ' ').replace('\n', ' '))
            except:
                toked_bug = re.split(r"([.,!?;(){}])", ' '.join(abstract_class))
                toked_bug = ' '.join(toked_bug).replace('< START_BUG >', '<START_BUG>').replace('< END_BUG >',
                                                                                                '<END_BUG>')
                if not ("<START_BUG>" in toked_bug and "<END_BUG>" in toked_bug):
                    exit(1)
                    failed_ids.append(id)
                    print("fail",id)
                else:
                    success_ids.append(id)
                    abstracted_lines.append(toked_bug.strip().replace('\r\n',' ').replace('\n',' '))

    print(len(failed_ids),failed_ids)
    print(len(success_ids),success_ids)
    writeLines(success_ids,output_prefix+"_ids.txt")
    writeLines(abstracted_lines,output_prefix+"_buggy.txt")
def process2deval_format(pred_file_f,bugs_loc_f,output_dir,candidate_size=300):
    pred_lines = read_Lines (pred_file_f)
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
            write_oriLines(patched_file_lines,tgt_path)
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
        writeJson(meta_infos,os.path.join(output_dir,bugid,bugid+".SequenceR.patchinfo.json"))
#preprocess_SequenceR_Buggy_deval("/home/debugeval/NPR4J_Result/data/npr4j_additional_bug_loc_statistics.json","/home/debugeval/NPR4J_Result/results/sequenceR/tmp",
                              #"/home/debugeval/NPR4J_Result/results/sequenceR/additional",
                              #"../../lib-jar/abstraction-1.0-SNAPSHOT-jar-with-dependencies.jar")
process2deval_format("/home/debugeval/NPR4J_Result/results/sequenceR/add_bugs.pred",
                     "/home/debugeval/NPR4J_Result/data/npr4j_additional_bug_loc_statistics.json",
                     "/home/debugeval/NPR4J_Result/results/sequenceR/deval")