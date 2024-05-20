from tree_sitter import Language, Parser
from Utils import ExtractContent

Language.build_library(
    # Store the library in the `build` directory
    "build/my-languages.so",
    # Include one or more languages
    ["/home/debugeval/tree-sitter-java"],
)
JAVA_LANGUAGE = Language("build/my-languages.so", "java")
java_parser = Parser()
java_parser.set_language(JAVA_LANGUAGE)

def isHunkContinual(line_ids: list):
    if len(line_ids) == 1:
        return True
    else:
        last_id = line_ids[0]
        for id in line_ids[1:]:
            if id - last_id == 1:
                pass
            else:
                return False
    return True

def find_buggymethod_java(file_path,start_line,end_line):
    java_class = ExtractContent.readfile4treesitter(file_path)
    tree = java_parser.parse(java_class)
    root_node = tree.root_node
    query = JAVA_LANGUAGE.query("""
    (method_declaration
      name: (identifier) @function.method)
      """)
    captures = query.captures(root_node, (start_line, 0))
    for c in captures:
        md= c[0].parent()
        md_start_line = md.start_point[0]
        md_end_line = md.end_point[0]
        if md_start_line<=start_line and md_end_line>=end_line:
            return md_start_line,md_end_line
    return None,None
