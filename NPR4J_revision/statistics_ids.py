from Utils.ExtractContent import readJson, readLines, writeJson


def count_ids(original_ids_f,output_f):
    ori_ids =readLines(original_ids_f)
    d4j_info = readJson(r"E:\NPR4J\MongoDB_output\Binfo_d4j.json")
    bears_info = readJson(r"D:\文档\icse2023\bears_result.json")

    npr4j_ori_ids = {"Defects4j":[],"Bears":[],"QuixBugs":[]}
    for id in ori_ids:
        bench,pure_id = id.split("_")
        print(bench,id)
        if bench == "d4j":
            for item in d4j_info:
                if pure_id.strip()==item["_id"]["$oid"]:
                    bugname = "_".join(item["parent_id"].split("/")[-1].split("_")[:2])
                    npr4j_ori_ids["Defects4j"].append(bugname.replace("_","-"))
            #print(len(npr4j_ori_ids["Defects4j"]))
        elif bench == "bears":
            for bugname in bears_info.keys():
                ids=bears_info[bugname]["ids"]
                if id in ids:
                    npr4j_ori_ids["Bears"].append(bugname)
            #print(len(npr4j_ori_ids["Bears"]))
    print(len(npr4j_ori_ids["Defects4j"]))
    print(len(npr4j_ori_ids["Bears"]))
    writeJson(npr4j_ori_ids,output_f)
count_ids("D:\文档\icse2023\oneline_ids2.txt","NPR4j_ori_ids.json")





