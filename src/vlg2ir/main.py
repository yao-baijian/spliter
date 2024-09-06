from __future__ import absolute_import
from __future__ import print_function
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from AST_analyzer import *
from pyverilog.vparser.parser import parse
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

designlist = ['aes_cipher_top',
              'fir_guide',
              'divider_cell_unwrap', 
              'divider_cell', 
              'divider_cell_synth', 
              'aes_cipher_top_synth', 
              'TinyRocket_sog']

mode = ''

design = designlist[0]
design_path = 'work/' + design + '.v'

if not os.path.exists(design_path):
    raise IOError("file not found: " + design_path)

ast, directives = parse([design_path], preprocess_include=[], preprocess_define=[])

if mode == 'example':
    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)
    with open("src/vlg2ir/result/ast2verilog_example.v", "w") as f:
        f.write(rslt)
        f.close()

else:
    with open("src/vlg2ir/result/" + design + "_ast.txt", "w") as f:
        ast.show(buf = f)
        
    ast_analyzer = AST_analyzer(ast)
    ast_analyzer.AST2Graph(ast)

    # Find the critical path and generate Verilog code for both parts
    ast_analyzer.graph.partition_graph(design)
