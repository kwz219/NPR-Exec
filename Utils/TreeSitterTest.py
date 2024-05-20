from tree_sitter import Language, Parser


import ExtractContent
Language.build_library(
    # Store the library in the `build` directory
    "build/my-languages.so",
    # Include one or more languages
    ["/home/debugeval/tree-sitter-java"],
)
JAVA_LANGUAGE = Language("build/my-languages.so", "java")
parser = Parser()
parser.set_language(JAVA_LANGUAGE)
class4test = ExtractContent.readfile4treesitter("../TestExamples/AbstractCategoryItemRenderer.java.buggy")
tree = parser.parse(
class4test
)
print(tree)
root_node = tree.root_node

print(root_node.start_point,root_node.end_point)
print(root_node.start_byte,root_node.end_byte)
query = JAVA_LANGUAGE.query("""
(method_declaration
  name: (identifier) @function.method)
  """)

captures = query.captures(root_node,(1797,0))
print(len(captures))
for c in captures:
    print(c[0].parent.type,c[0].type,c[0].text,c[0].start_point,c[0].end_point)
    print(c[0].parent.start_point,c[0].parent.end_point)