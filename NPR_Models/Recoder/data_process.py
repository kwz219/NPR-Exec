import codecs
import json
import os
from subprocess import Popen, PIPE

import javalang
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
def generate_classcontent(path, output_path, filename):
    codecontent=codecs.open(path,'r',encoding='utf8').read().strip()
    #print(codecontent)
    tree = javalang.parse.parse(codecontent)
    package_name=tree.package.name
    #print(package_name)
    #print(tree)
    i=1

    classcontent={"filename":filename,"package_name":package_name,"classes":[]}
    for clspath,clsnode in tree.filter(javalang.tree.ClassDeclaration):
        classname=getattr(clsnode,"name")
        #print("classname: ",classname)
        class_dict = {"methods": [], "fields": [], "name":classname}
        for path,node in clsnode.filter(javalang.tree.MethodDeclaration):
            node_name = getattr(node, "name")
            return_type = getattr(node, "return_type")
            if return_type == None:
                return_type_name = None
            else:
                return_type_name = getattr(return_type, "name")
            parameters = getattr(node, "parameters")
            if len(parameters) == 0:
                simp_parameters = []
            else:
                simp_parameters = []
                for pa in parameters:
                    pa_name = getattr(pa, "name")
                    pa_type = getattr(getattr(pa, "type"), "name")
                    pa_item = {"name": pa_name, "type": pa_type}
                    simp_parameters.append(pa_item)
            method_dict = {"params": simp_parameters, "name": node_name,"type":return_type_name}
            #print("$", "methods", "$ -------------------------")
            #print(node_name)
            #print(simp_parameters)
            #print(return_type_name)
            i = i + 1

            new_methods=class_dict.get("methods")
            new_methods.append(method_dict)
            #print("new_methods",new_methods)
            class_dict["methods"]=new_methods
            #print(class_dict["methods"])

        for path,node in clsnode.filter(javalang.tree.FieldDeclaration):
            field_dec=getattr(node,"declarators")
            field_type=getattr(node,"type")

            field_name=getattr(field_dec[0],"name")
            field_type_name=getattr(field_type,"name")

            #print("$", "Field", "$ -------------------------")
            #print(field_name)
            #print(field_type_name)
            i+=1
            field_dict={"name":field_name,"type":field_type_name}
            new_fields=class_dict.get("fields")
            new_fields.append(field_dict)
            class_dict["fields"]=new_fields
        new_classes=classcontent.get("classes")

        new_classes.append(class_dict)
        classcontent["classes"]=new_classes
    with open(output_path,"w",encoding='utf8')as f:
        json.dump([classcontent],f,indent=2)


def patchMethod2File(pure_patch,buggy_file_path,buggy_lines):
    start_line = buggy_lines[0]
    end_line = buggy_lines[-1]
    m_s,m_e=bc.find_buggymethod_java(buggy_file_path,start_line,end_line)
    class_lines = read_oriLines(buggy_file_path)
    patched_lines = class_lines[:m_s]+[pure_patch]+class_lines[m_e+1:]
    return patched_lines

def process2deval_format(pred_dir,bugs_loc_f,output_dir,candidate_size=300):

    pred_files = os.listdir(pred_dir)
    bugs_locs = readJson(bugs_loc_f)
    for file in pred_files:
        if str(file).endswith(".fix"):
            meta_infos = []
            bug_id = file.replace(".fix","").strip()
            bug_id = bug_id.replace("_SEP_","<SEP>")
            if not bug_id in list(bugs_locs.keys()):
                continue
            file_path = os.path.join(pred_dir,file)
            file_info = readJson(file_path)
            bug_info = bugs_locs[bug_id][0]
            file_name = bug_info["file_rel_path"].split("/")[-1].replace(".java", "")
            buggy_file_path = bug_info["file_content_path"]
            buggy_lines = bug_info["buggy_line_ids"]
            if not os.path.exists(os.path.join(os.path.join(output_dir, bug_id))):
                os.mkdir(os.path.join(output_dir, bug_id))
            for ind in file_info.keys():
                pure_patch = file_info[ind]
                patched_file_lines = patchMethod2File(pure_patch,buggy_file_path,buggy_lines)
                tgt_path = os.path.join(os.path.join(output_dir, bug_id, file_name + "." + str(int(ind) + 1) + ".patch"))
                write_oriLines(patched_file_lines,tgt_path)
                meta_infos.append({
                    "bug_id": bug_id,
                    "patch_index": int(ind)+1,
                    "patch_contents":
                        [
                            {
                                "relative_file_position": bug_info["file_rel_path"],
                                "patch_content_position": tgt_path}
                        ]
                })
            writeJson(meta_infos, os.path.join(output_dir, bug_id, bug_id + ".Recoder.patchinfo.json"))

process2deval_format("/home/debugeval/NPR4J_Result/results/recoder_result",
                     "/home/debugeval/NPR4J_Result/data/npr4j_additional_bug_loc_statistics.json",
                     "/home/debugeval/NPR4J_Result/results/recoder",
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                )

