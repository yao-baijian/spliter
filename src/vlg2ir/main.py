from __future__ import absolute_import
from __future__ import print_function
import networkx as nx
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from AST_analyzer import *
from pyverilog.vparser.parser import parse

designlist = ['work/aes_cipher_top.v', 'work/TinyRocket_sog.v']

design = designlist[0]
if not os.path.exists(design):
    raise IOError("file not found: " + design)
        
ast, directives = parse([design], 
                        preprocess_include=[], 
                        preprocess_define=[])
with open("src/vlg2ir/ast.out/ast.txt", "w") as f:
    ast.show(buf = f)

ast_analyzer = AST_analyzer(ast)
ast_analyzer.AST2Graph(ast)

# Find the critical path and generate Verilog code for both parts
ast_analyzer.graph.partition_graph('aes_improve')
