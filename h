[1mdiff --git a/src/compiler/ast_/loop.py b/src/compiler/ast_/loop.py[m
[1mindex 0f35e53..7471373 100644[m
[1m--- a/src/compiler/ast_/loop.py[m
[1m+++ b/src/compiler/ast_/loop.py[m
[36m@@ -65,9 +65,7 @@[m [mclass LoopBody(Node):[m
         ][m
 [m
         for index, definition in enumerate(self.statements):[m
[31m-            self.add_sub_ir([m
[31m-                        definition.value.build([self.out_ports[index]], scope)[m
[31m-                    )[m
[32m+[m[32m            self.add_sub_ir(definition.value.build([self.out_ports[index]], scope))[m
             # here we add newly defined value to the scope[m
             value_port = Edge.src_port(self.out_ports[index])[m
             # TODO add option to not change port's label and rather[m
