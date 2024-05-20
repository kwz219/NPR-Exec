from Utils.ExtractContent import readJson

DebugEval_Data_Dir = ""

def getDevalBugInfos(ids_f,locs_f):
    ids_dict = readJson(ids_f)
    locations = readJson(locs_f)
    bug_infos = {}
    for bench in ids_dict.keys():
        ids = ids_dict[bench]
        for id in ids:
            bug_infos[id]=locations[id]
            print(id)
            pass
    return bug_infos
