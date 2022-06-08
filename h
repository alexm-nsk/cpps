[1mdiff --git a/src/compiler/ast_/array_access.py b/src/compiler/ast_/array_access.py[m
[1mindex 163aca8..c10af5a 100644[m
[1m--- a/src/compiler/ast_/array_access.py[m
[1m+++ b/src/compiler/ast_/array_access.py[m
[36m@@ -42,8 +42,10 @@[m [mclass ArrayAccess(Node):[m
         array_ir = self.array.build([self.in_ports[0]], scope)[m
         # TODO assert its actually an array and put out an error[m
         # if it isn't[m
[32m+[m[32m        # TODO assert there is one edge in array_ir's output_edges[m
[32m+[m
         self.out_ports[0].type = array_ir.output_type().element_type()[m
[31m-        #print("test")[m
[32m+[m
         nodes = [self][m
         indices_ir = SubIr([], [], [])[m
         edges = [][m
[36m@@ -68,7 +70,7 @@[m [mclass ArrayAccess(Node):[m
         del self.index[m
 [m
         return ([m
[31m-            SubIr(nodes=[self]+nodes, output_edges=[], internal_edges=edges)[m
[32m+[m[32m            SubIr(nodes=nodes, output_edges=[], internal_edges=edges)[m
             + array_ir[m
             + indices_ir[m
         )[m
