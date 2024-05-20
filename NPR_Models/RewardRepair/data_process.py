import json
import os
import re
import shutil

import javalang
from subprocess import Popen, PIPE


import BugCharacter as bc
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

def process2deval_format(pred_file_f,bugs_loc_f,output_dir,candidate_size=300):
    pred_lines = read_oriLines (pred_file_f)
    bugs_locs = readJson(bugs_loc_f)
    bugnum = len(bugs_locs)
    assert bugnum*candidate_size == len(pred_lines)

    ids = list(bugs_locs.keys())

    for idx,id in enumerate(ids):
        bug_preds = pred_lines[idx*candidate_size:(idx+1)*candidate_size]
        bug_index = int(bug_preds[0].split()[0])
        bugid  = ids[bug_index]

        #making dirs for saving formatted files
        if not os.path.exists(os.path.join(os.path.join(output_dir,bugid))):
            os.mkdir(os.path.join(output_dir,bugid))
            # prepare patched file and their meta information
            meta_infos = []
            bug_info = bugs_locs[bugid][0]
            file_content_path = bug_info["file_content_path"]
            buggy_lines = bug_info["buggy_line_ids"]
            file_name = bug_info["file_rel_path"].split("/")[-1].replace(".java", "")
            patch_candidates = pred_lines[idx * candidate_size:(idx + 1) * candidate_size]

            for candid, cand_content in enumerate(patch_candidates):
                parts = cand_content.split('\t')
                if len(parts)==2:
                    pure_patch = parts[1]
                else:
                    pure_patch = '\t'.join(parts[1:])

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
            writeJson(meta_infos, os.path.join(output_dir, bugid, bugid + ".RewardRepair.patchinfo.json"))


def preprocess_RewardRepair_deval(bug_loc_file,tmp_dir,output_prefix,jar_path):
    bug_loc_infos = readJson(bug_loc_file)
    ids = list(bug_loc_infos.keys())
    bug_fix = []
    error_ids = []
    success_ids = []
    bug_fix.append("bugid" + '\t' + "store_id" + '\t' + "buggy" + '\t' + "patch")
    if True:
        for idx, id in enumerate(ids):

            bug_info = bug_loc_infos[id]
            buggy_file_info = bug_info[0]
            err_lines = buggy_file_info["buggy_line_ids"]
            err_start = err_lines[0]
            err_end = err_lines[-1]

            buggy_file_path = buggy_file_info["file_content_path"]

            print("error line ids", err_start, err_end)
            "generate abstract file of buggy class"
            file_name = buggy_file_path.split("/")[-1].replace(".java.buggy","")
            shutil.copyfile(buggy_file_path,buggy_file_path.replace(".buggy",""))
            buggy_class_f = buggy_file_path.replace(".buggy","")
            output_f = tmp_dir + '/' + file_name + '.java'
            args = [jar_path, buggy_class_f, output_f]
            if not os.path.exists(output_f):
                out, err = jarWrapper(args)
                print("out",out)
                print("err",err)

            m_start_line, m_end_line = bc.find_buggymethod_java(buggy_class_f,err_start,err_end)



            class_lines = read_Lines(buggy_class_f)
            print("m_position", m_start_line, m_end_line)

            if (m_start_line == None):
                if err_start == err_end:
                    buggy_line = class_lines[err_start]
                else:
                    buggy_line = class_lines[err_start:err_end+1]
                if type(buggy_line) == list:
                    clean_line = ' '.join(buggy_line)
                else:
                    clean_line = buggy_line

                clean_line = re.sub('\s+', ' ', clean_line)
                clean_context = re.sub('\s+', ' ', ' '.join(class_lines))
                buggy_src = "buggy: " + clean_line + " context: " + clean_context

                bug_fix.append(str(len(bug_fix) - 1) + '\t' + id + '\t' + buggy_src + '\t' + '<BLANK>')
                success_ids.append(id)
                continue


            method_lines = class_lines[m_start_line:m_end_line+1]

            rel_err_start = err_start - m_start_line -1
            rel_err_end = err_end - m_start_line -1
            if err_start == err_end:
                buggy_line = method_lines[rel_err_start]

            else:
                buggy_line = method_lines[rel_err_start:rel_err_end + 1]

            print(id,"buggy_line", buggy_line)

            "generate 3-level abstract file"
            abstract_class = []
            success_flag = 0
            error_start_in_class = err_start
            error_end_in_class = err_end
            try:

                for idx, line in enumerate(class_lines):
                    check_line = method_lines[0].replace("<START_BUG>", "").replace("<END_BUG>", "")
                    if check_line.strip() in line.strip():
                        print(idx)
                        abstract_class = class_lines[:idx] + method_lines + class_lines[idx + 1:]
                        success_flag = 1
                        error_start_in_class = idx + error_start_in_class
                        error_end_in_class = idx + error_end_in_class
                        break

                print(len(abstract_class))
                clean_class = []
                ori_error_start_in_class = error_start_in_class
                ori_error_end_in_class = error_end_in_class
                # print(abstract_class)
                print("error position in class:", error_start_in_class, error_end_in_class)
                print("buggy line in class:", abstract_class[error_start_in_class].strip(),
                      abstract_class[error_end_in_class].strip())

                for idx, line in enumerate(abstract_class):
                    line4check = str(line.strip())
                    if line4check.startswith("/") or line4check.startswith(
                            "*") or line4check == "" or line4check == r"*/":
                        if idx < ori_error_start_in_class:
                            error_start_in_class = error_start_in_class - 1
                            error_end_in_class = error_end_in_class - 1
                        elif idx >= ori_error_start_in_class and idx <= ori_error_end_in_class:
                            clean_class.append(line)
                    else:
                        # print(line.strip())
                        clean_class.append(line)

                # print(clean_class)
                # print(error_start_in_class,error_end_in_class)
                print("error_line_inclean: ", clean_class[error_start_in_class].strip(),
                      clean_class[error_end_in_class].strip())

                if success_flag == 1:

                    def truncate(class_lines, err_start, err_end, max_length=1000):
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
                            while end_pos > err_end:
                                total_length = sum(length_list[:end_pos])
                                if total_length <= max_length:
                                    cur_len_satisfy = True
                                    break
                                else:
                                    end_pos = end_pos - 1
                            if cur_len_satisfy:
                                return class_lines[:end_pos]
                            else:
                                start_pos = 0
                                while start_pos > err_start:
                                    total_len = sum(length_list[start_pos:end_pos])
                                    if total_len <= max_length:
                                        return class_lines[start_pos:end_pos]
                                    else:
                                        start_pos += 1
                                return class_lines[start_pos:end_pos]

                    abstract_class = truncate(clean_class, error_start_in_class, error_end_in_class)

                else:
                    abstract_class = method_lines

                "tokenize source codes"

                clean_line = ''
                if type(buggy_line) == list:
                    clean_line = ' '.join(buggy_line)
                else:
                    clean_line = buggy_line

                clean_line = re.sub('\s+', ' ', clean_line)
                clean_context = re.sub('\s+', ' ', ' '.join(abstract_class))
                buggy_src = "buggy: " + clean_line + " context: " + clean_context

                bug_fix.append(str(len(bug_fix) - 1) + '\t' + id + '\t' + buggy_src + '\t' + '<BLANK>')

                success_ids.append(id)



            except:

                if type(buggy_line) == list:
                    clean_line = ' '.join(buggy_line)
                else:
                    clean_line = buggy_line

                clean_line = re.sub('\s+', ' ', clean_line)
                clean_context = re.sub('\s+', ' ', ' '.join(abstract_class))
                buggy_src = "buggy: " + clean_line + " context: " + clean_context

                bug_fix.append(str(len(bug_fix) - 1) + '\t' + id + '\t' + buggy_src + '\t' + '<BLANK>')
                success_ids.append(id)

        writeLines(bug_fix, output_prefix + '.bug-fix.csv')
        writeLines(error_ids, output_prefix + '.fids')
        writeLines(success_ids, output_prefix + '.ids')

def preprocess_RewardRepair_fromRaw_simple(buggy_methods_dir,buggy_class_dir,output_prefix,tmp_dir,jar_path):
    ids=os.listdir(buggy_methods_dir)
    bug_fix=[]
    error_ids = []
    success_ids = []
    bug_fix.append("bugid" +'\t'+"store_id"+ '\t' + "buggy" + '\t' + "patch")
    for idx,id in enumerate(ids):
        id = id.replace('.txt','')
        # e.g. of id: Chart_TimePeriodValues_43-46
        infos = id.split("_")
        err_lines = infos[2]
        err_start = -1
        err_end = -1
        if "-" in err_lines:
            start_end = err_lines.split("-")
            err_start = int(start_end[0])
            err_end = int(start_end[1])
        else:
            err_start = int(err_lines)
            err_end = int(err_lines)

        print("error line ids", err_start, err_end)
        "generate abstract file of buggy class"
        classname = infos[0]+"_"+infos[1]
        buggy_class_f = buggy_class_dir + '/' + classname + '.java'
        output_f = tmp_dir + '/' +classname+ '.java'
        args = [jar_path, buggy_class_f, output_f]
        if not os.path.exists(output_f):
            out, err = jarWrapper(args)


        method_lines = readF2L(buggy_methods_dir + '/' + id + '.txt')
        if err_start == err_end:
            buggy_line = method_lines[err_start]

        else:
            buggy_line = method_lines[err_start:err_end + 1]
        print("buggy_line", buggy_line)

        "generate 3-level abstract file"
        abstract_class = []
        success_flag = 0
        error_start_in_class = err_start
        error_end_in_class = err_end
        try:
            class_lines = readLines(output_f)

            for idx, line in enumerate(class_lines):

                check_line = method_lines[0].replace("<START_BUG>", "").replace("<END_BUG>", "")

                if check_line.strip() in line.strip():
                    print(idx)
                    abstract_class = class_lines[:idx] + method_lines + class_lines[idx + 1:]
                    success_flag = 1
                    error_start_in_class = idx + error_start_in_class
                    error_end_in_class = idx + error_end_in_class
                    break

            print(len(abstract_class))
            clean_class = []
            ori_error_start_in_class = error_start_in_class
            ori_error_end_in_class = error_end_in_class
            # print(abstract_class)
            print("error position in class:", error_start_in_class, error_end_in_class)
            print("buggy line in class:", abstract_class[error_start_in_class].strip(),
                  abstract_class[error_end_in_class].strip())

            for idx, line in enumerate(abstract_class):
                line4check = str(line.strip())
                if line4check.startswith("/") or line4check.startswith("*") or line4check == "" or line4check == r"*/":
                    if idx < ori_error_start_in_class:
                        error_start_in_class = error_start_in_class - 1
                        error_end_in_class = error_end_in_class - 1
                    elif idx >= ori_error_start_in_class and idx <= ori_error_end_in_class:
                        clean_class.append(line)
                else:
                    # print(line.strip())
                    clean_class.append(line)

            # print(clean_class)
            # print(error_start_in_class,error_end_in_class)
            print("error_line_inclean: ", clean_class[error_start_in_class].strip(),
                  clean_class[error_end_in_class].strip())

            if success_flag == 1:


                def truncate(class_lines, err_start, err_end, max_length=1000):
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
                        while end_pos > err_end:
                            total_length = sum(length_list[:end_pos])
                            if total_length <= max_length:
                                cur_len_satisfy = True
                                break
                            else:
                                end_pos = end_pos - 1
                        if cur_len_satisfy:
                            return class_lines[:end_pos]
                        else:
                            start_pos = 0
                            while start_pos > err_start:
                                total_len = sum(length_list[start_pos:end_pos])
                                if total_len <= max_length:
                                    return class_lines[start_pos:end_pos]
                                else:
                                    start_pos += 1
                            return class_lines[start_pos:end_pos]

                abstract_class = truncate(clean_class, error_start_in_class, error_end_in_class)

            else:
                abstract_class = method_lines

            "tokenize source codes"

            clean_line=''
            if type(buggy_line)==list :
                clean_line = ' '.join(buggy_line)
            else:
                 clean_line =buggy_line

            clean_line =re.sub('\s+',' ',clean_line)
            clean_context = re.sub('\s+',' ',' '.join(abstract_class))
            buggy_src = "buggy: "+clean_line + " context: "+clean_context

            bug_fix.append(str(len(bug_fix)-1)+'\t'+id+'\t'+buggy_src+'\t'+'<BLANK>')

            success_ids.append(id)



        except:
            method_lines = readLines(buggy_methods_dir + '/' + id + '.txt')
            if type(buggy_line)==list :
                clean_line = ' '.join(buggy_line)
            else:
                 clean_line =buggy_line

            clean_line =re.sub('\s+',' ',clean_line)
            clean_context = re.sub('\s+',' ',' '.join(abstract_class))
            buggy_src = "buggy: "+clean_line + " context: "+clean_context

            bug_fix.append(str(len(bug_fix)-1)+'\t'+id+'\t'+buggy_src+'\t'+'<BLANK>')
            success_ids.append(id)

    writeLines(bug_fix, output_prefix + '.bug-fix.csv')
    writeLines(error_ids, output_prefix + '.fids')
    writeLines(success_ids, output_prefix + '.ids')

#preprocess_RewardRepair_deval("/home/debugeval/NPR4J_Result/data/npr4j_additional_bug_loc_statistics.json",
                              #"/home/debugeval/NPR4J_Result/results/RewardRepair/tmp",
                              #"/home/debugeval/NPR4J_Result/results/RewardRepair/addtional",
                              #"../../lib-jar/abstraction-1.0-SNAPSHOT-jar-with-dependencies.jar")

process2deval_format("/home/debugeval/NPR4J_Result/results/RewardRepair/additional.bug-fix.pred",
                         "/home/debugeval/NPR4J_Result/data/npr4j_additional_bug_loc_statistics.json",
                         "/home/debugeval/NPR4J_Result/results/RewardRepair/deval")
