import re
import json

def readLines(file_path):
    lines = []
    with open(file_path,'r',encoding='utf8')as f:
        for line in f:
            lines.append(line.strip())
        f.close()
    return lines
def extractSingleHunkCode(file,buggy_line_ids:list):
    codes = readLines(file)
    hunk_lines = []
    for id in buggy_line_ids:
        buggy_line = re.sub('\s+',' ',codes[id-1])
        hunk_lines.append(buggy_line)
    return '\n'.join(hunk_lines)

def writeLines(lines,file):
    with open(file,'w',encoding='utf8')as f:
        for line in lines:
            f.write(line+'\n')
        f.close()


def readJson(file_path):
    with open(file_path,'r',encoding='utf8')as f:
        result=json.load(f)
    return result

def writeJson(dic_result,output_path):
    with open(output_path,'w',encoding='utf8')as f:
        json.dump(dic_result,f,indent=4)

def readfile4treesitter(file_path):
    with open(file_path,'rb')as f:
        data = f.read()
        f.close()
    return data
    pass
