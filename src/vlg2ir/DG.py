
from collections import defaultdict
from multiprocessing import Pool
from pyverilog.vparser.ast import *
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
import sys, re, os
import numpy as np
import pickle
from funcy import *
sys.setrecursionlimit(10000)

class Node:
    def __init__(self, name, type, width:None, father:None):
        self.name = name
        self.type = type 
        self.width = width
        self.father = father
        self.path = []
        self.tr = None
        self.t1 = 0.5
    
    def update_width(self, width):
        self.width = width
    
    def update_delay(self, delay):
        self.delay = delay
        
    def update_fanout(self, fanout):
        self.fanout = fanout
    
    def update_feature(self, feat):
        self.feat = feat
    
    def update_AT(self, AT_delay, path, visited=False):
        if visited:
            # self.AT = max(self.AT-self.delay, AT_delay) + self.delay
            if self.AT-self.delay < AT_delay:
                self.AT = AT_delay
                self.path = path

        else:
            self.AT = AT_delay + self.delay
            path_copy = path.copy()
            path_copy.append(self.name)
            self.path = path_copy
    
    def update_AT_transformer(self, AT_delay, path, fanout_num,visited=False):
        if visited:
            # self.AT = max(self.AT-self.delay, AT_delay) + self.delay
            if self.AT-self.delay < AT_delay:
                self.AT = AT_delay
                self.path = path

        else:
            self.AT = AT_delay + self.delay
            path_copy = path.copy()
            path_copy.append(self.name)
            self.path = path_copy

    def finish_AT(self):
        if self.path[-1] != self.name:
            self.path.append(self.name)
            self.AT += self.delay
        p_s = re.sub(r'_CK_$', '', self.path[-1])
        p_s = re.sub(r'_Q_$', '', p_s)
        p_e = re.sub(r'_CK_$', '', self.path[0])
        p_e = re.sub(r'_Q_$', '', p_e)
        pair = (p_s, p_e)

        return pair, self.path, self.AT

    def add_tr(self, tr):
        self.tr = tr
    
    def add_t1(self, t1):
        self.t1 = t1
    
    def __repr__(self):
        return self.name

class Graph:
    def __init__(self):
        self.graph = defaultdict(list)
        self.node_dict = {}

    def init_graph(self, graph, node_dict):
        self.graph = graph
        self.node_dict = node_dict

    def add_decl_node(self, name, type, width=None, father=None):
        node = Node(name, type, width, father)
        self.node_dict[name] = node

    def graph2pkl(self, design_name, cmd, folder_dir):
        graph_name = folder_dir + f'{design_name}_{cmd}.pkl'
        node_dict_name = folder_dir + f'{design_name}_{cmd}_node_dict.pkl'
        with open(graph_name, 'wb') as f:
            pickle.dump(self.graph, f)
        with open(node_dict_name, 'wb') as f:
            pickle.dump(self.node_dict, f)
    
    def add_edge(self, u, v):
        if u not in self.graph:
            self.graph[u] = []
        self.graph[u].append(v)
    
    def remove_node(self, u):
        if u in self.graph.copy():
            del self.graph[u]
    
    def get_neighbors(self, u):
        return self.graph[u]
    
    def get_all_nodes(self):
        return self.graph.keys()
    
    def get_all_nodes2(self):
        all_nodes = set()
        for key, val_list in self.graph.items():
            all_nodes.add(key)
            for var in val_list:
                all_nodes.add(var)
        return all_nodes

    def load_node_dict(self, node_dict):
        self.node_dict = node_dict
    
    def cal_node_width(self):
        print('----- Calculating Operator Width -----')
        self.nowidth_set = set()
        for name, node in self.node_dict.items():
            if not node.width:
                self.nowidth_set.add(name)

        while(len(self.nowidth_set) != 0):
            ll_pre = len(self.nowidth_set)
            for n in self.nowidth_set.copy():
                # print(n)
                # assert n in self.graph.keys()
                if n in self.graph.keys():
                    neighbor = self.graph[n]
                    width = self.get_max_neighbor_width(neighbor)
                    self.node_dict[n].update_width(width)
                    if width:
                        self.nowidth_set.remove(n)
            ll_post = len(self.nowidth_set)
        #     if ll_pre == ll_post:
        #         break
        # print(ll_post)
        # print(self.nowidth_set)

    def get_max_neighbor_width(self, neighbor):
        width_list = []
        for n in neighbor:
            width_node = self.node_dict.get(n)
            if not width_node:
                return width_node
            else:
                width = width_node.width
                if (not width):
                    self.get_max_neighbor_width(n)
                width_list.append(width)
                
        assert len(neighbor) == len(width_list)
        width = max(width_list)
        return width
    
    def get_stat(self):
        all_node = self.get_all_nodes2()
        self.seq_set = set()
        self.wire_set = set()
        self.comb_set = set()
        self.in_set = set()
        self.out_set = set()
        type_set = set()
        seq_num = 0
        comb_num = 0
        for name, node in self.node_dict.items():
            ntype = node.type
            if ntype == 'Reg':
                self.seq_set.add(name)
            elif ntype == 'Wire':
                self.wire_set.add(name)
            elif ntype in ['Operator', 'UnaryOperator', 'Concat', 'Repeat']:
                self.comb_set.add(name)
            elif ntype in ['Input']:
                self.in_set.add(name)
            elif ntype in ['Output']:
                self.in_set.add(name)

        for name, node in self.node_dict.items():
            father = node.father
            if father:
                if self.node_dict[father].type == 'Reg':
                    self.seq_set.add(name)
                elif self.node_dict[father].type == 'Wire':
                    self.wire_set.add(name)
                elif self.node_dict[father].type == 'Input':
                    self.in_set.add(name)
                elif self.node_dict[father].type == 'Output':
                    self.out_set.add(name)           
    
    def show_graph(self):
        self.get_stat()
        print('----- Writting Graph Visialization File -----')
        outfile_path = "../img/"
        outfile = outfile_path+"AST_graph.dot"
        top_name = 'test'
        node_set = self.get_all_nodes2()
        pair_set = set()
        for vertice in self.graph.keys():
            node_set.add(vertice)
            val_list = self.get_neighbors(vertice)
            for val in val_list:
                if val:
                    if vertice:
                        val = re.sub(r'\.|\[|\]|\\', r'_', val)
                        vertice = re.sub(r'\.|\[|\]|\\', r'_', vertice)
                        pair = '{0} -> {1}'.format(vertice, val)
                        pair_set.add(pair)

        with open (outfile, 'w') as f:
            line = "digraph {0} ".format(top_name)
            line = line + "{\n"
            f.write(line)
            reg_set = set()
            for node in node_set:
                if not node:
                    break
                n = self.node_dict[node]
                ntype = n.type
                node1 = re.sub(r'\.|\[|\]|\\', r'_', node)
                if node in self.seq_set:
                    line = "    {0} [style=filled, color=lightblue];\n".format(node1)
                elif node in self.wire_set:
                    line = "    {0} [style=filled, color=red];\n".format(node1)
                elif node in self.in_set:
                    line = "    {0} [style=filled, color=black];\n".format(node1)
                elif node in self.out_set:
                    line = "    {0} [style=filled, color=green];\n".format(node1)
                elif ntype == 'Constant':
                    line = "    {0} [style=filled, color=grey];\n".format(node1)
                elif node in self.comb_set:
                    line = "    {0} [style=filled, color=pink];\n".format(node1)

                else:
                    line = "    {0};\n".format(node1)
                f.write(line)
            for pair in pair_set:
                line = "    {0};\n".format(pair)
                f.write(line)
            
            f.write("}\n")
        
        print('Finish!\n')

    def find_critical_path(self):
        # 找到所有Reg节点
        reg_nodes = [name for name, node in self.node_dict.items() if node.type == 'Reg']
        critical_path = []
        orphan_regs = []

        # 遍历所有Reg节点，找到所有Reg-Reg之间的最短路径
        for start_node in reg_nodes:
            for end_node in reg_nodes:
                if start_node != end_node:
                    path = self.find_shortest_path(start_node, end_node)
                    if path:
                        critical_path.append(path)
                        
        for reg in reg_nodes:
            has_parent = False
            for node in self.node_dict.values():
                if reg in self.get_neighbors(node.name):
                    has_parent = True
                    break
            if not has_parent:
                orphan_regs.append(reg)
                
        return critical_path if len(critical_path) != 0 else None, orphan_regs if len(orphan_regs) != 0 else None

    def get_parent_nodes(self, node):
        # TODO add parent nodes search
        self.get_neighbors(self, node)
    
    
    
    def find_shortest_path(self, start, end):
        # 使用BFS找到最短路径
        queue = [(start, [start])]
        visited = set()

        while queue:
            (node, path) = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)

            for neighbor in self.get_neighbors(node):
                if neighbor == end:
                    return path + [end]
                else:
                    queue.append((neighbor, path + [neighbor]))
        return None
    
    def construct(self, path, inst):
        
        if inst == 'Always':
            return Always(SensList(self.construct(path, 'SensList')), self.construct(path, 'Block'))
            
        elif inst == 'SensList':
            return [Sens(Identifier('clk'))]
        
        elif inst == 'Block':
            return  NonblockingSubstitution(self.construct(path, 'Lvalue'), self.construct(path, 'Rvalue'))
            
        elif inst == 'Lvalue':
            node =  path.pop(0)
            return Lvalue(Identifier(node))
        
        elif inst == 'Rvalue':
            node =  path.pop(0)
            if node[0:4] == 'Cond':
                path = self.get_neighbors(node)
                return Rvalue(self.construct(path, 'Cond'))
            else:
                return Rvalue(Identifier(node))
        elif inst == 'Cond':
            return Cond(self.construct(path[0], 'Elem'),
                        self.construct(path[1], 'Elem'),
                        self.construct(path[2], 'Elem'))
        elif inst == 'Elem':
            node = path
            if node[:-2] == 'Xor':
                path = self.get_neighbors(node)
                return Xor(Identifier(path[0]), Identifier(path[1]))
            else:
                return Identifier(node)
        else:
            return None


    def extract_critical_path_rtl(self, critical_paths, 
                                        orphan_regs, 
                                        params_list, 
                                        design_name, 
                                        post_fix ):
        items   = []
        params  = []
        ports   = []
        visited_output_port = []
        
        # name, width, dimensions, type,
        # get father node
        
        for param in params_list:
            params.append(ParamArg(param))
            
        for reg in orphan_regs:
            ports.append(Port(reg, Width(self.node_dict[reg].width, 0) , None, 'input'))
        
        for path in critical_paths:
            
            non_critical_father = []
            
            for node in path:
                # generate output reg
                if self.node_dict[node].type == 'Reg' and node not in orphan_regs and node not in visited_output_port:
                    visited_output_port.append(node)
                    ports.append(Port(node, Width(self.node_dict[reg].width, 0), None, 'output'))

                # check non-critial path father reg
                # parent_nodes = self.get_parent_nodes(node)
                # for parent in parent_nodes:
                #     if parent not in path:
                #         ports.append(Port(parent, Width(self.node_dict[parent].width, 0), None, 'input'))
                #         non_critical_father.append(parent)
            
            # operator = self.node_dict[path[1]]

            items.append(self.construct(path, 'Always'))
            
            ast = Source(None, 
                     ModuleDef(design_name + post_fix, 
                               Paramlist(params), 
                               Portlist(ports), 
                               items))
        # :  (at 135)
        #   Lvalue:  (at 135)
        #     Identifier: sa00 (at 135)
        #   Rvalue:  (at 135)
        #     Cond:  (at 135)
        #       Identifier: ld_r (at 135)
        #       Xor:  (at 135)
        #         Partselect:  (at 135)
        #           Identifier: text_in_r (at 135)
        #           IntConst: 127 (at 135)
        #           IntConst: 120 (at 135)
        #         Partselect:  (at 135)
        #           Identifier: w0 (at 135)
        #           IntConst: 31 (at 135)
        #           IntConst: 24 (at 135)
        #       Identifier: sa00_next (at 135)
        #   DelayStatement:  (at 135)
        #     IntConst: 1 (at 135)         
        
        codegen = ASTCodeGenerator()
        verilog_code = codegen.visit(ast)
        
        # 将 Verilog 代码写入文件
        with open(f"src/vlg2ir/result/{design_name}" + post_fix + ".v", "w") as f:
            f.write(verilog_code)

        return verilog_code

    def remove_critical_path(self, critical_paths):
        cp_node_dict = self.node_dict.copy()
        for path in critical_paths:
            for node in path:
                if self.node_dict[node].type != 'Reg':
                    self.remove_node(node)

        # 保留端寄存器
        for path in critical_paths:
            for node in path:
                if self.node_dict[node].type == 'Reg':
                    neighbors = self.get_neighbors(node)
                    for neighbor in neighbors:
                        if neighbor not in critical_paths:
                            self.add_edge(node, neighbor)
                                       
    def partition_graph(self, design_name):
        critical_path, orphan_regs = self.find_critical_path()
        if not critical_path:
            print("ERROR: pure comb logic")
            return 
        self.extract_critical_path_rtl(critical_path, orphan_regs, [], design_name, "_critical_paths")
        self.remove_critical_path(critical_path)
        self.extract_critical_path_rtl(critical_path, orphan_regs, [], design_name, "_remains")






     
                

