import os


def change_qbs(work_dir):
    dirs = os.listdir(work_dir)
    for dir in dirs:

        file_path = os.path.join(work_dir,dir,str(dir).upper()+".java.fixed")
        ori_lines = []
        with open(file_path,'r',encoding='utf8')as f:
            for line in f:
                new_line = line.replace("correct_java_programs","java_programs")
                ori_lines.append(new_line)
            f.close()

        with open(file_path,'w',encoding='utf8')as f:
            for line in ori_lines:
                f.write(line)
            f.close()
    pass
change_qbs("D:\文档\DebugEvalData\QuixBugs")