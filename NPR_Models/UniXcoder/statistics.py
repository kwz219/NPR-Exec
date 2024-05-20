import json
def readJson(file_path):
    with open(file_path,'r',encoding='utf8')as f:
        result=json.load(f)
    return result

def count_json(json_f):
    bugs_json = readJson(json_f)
    print(len(bugs_json))
    print(len(bugs_json)*300)

count_json(r"E:\NPR4J_Result\results\unixcoder_result\id_bug_match.json")

