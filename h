[1mdiff --git a/src/compiler/ast_/init.py b/src/compiler/ast_/init.py[m
[1mindex ff72b90..36f4e1b 100644[m
[1m--- a/src/compiler/ast_/init.py[m
[1m+++ b/src/compiler/ast_/init.py[m
[36m@@ -22,6 +22,5 @@[m [mclass Init(Node):[m
         self.name = "Init"[m
         self.statements = statements[m
 [m
[31m-    @build_method[m
[31m-    def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:[m
[31m-        pass[m
[32m+[m[32m    def build(self, scope: SisalScope) -> SubIr:[m
[32m+[m[32m        self.copy_ports(scope.node)[m
[1mdiff --git a/src/compiler/ast_/let.py b/src/compiler/ast_/let.py[m
[1mindex 74e9ebf..88bc102 100644[m
[1m--- a/src/compiler/ast_/let.py[m
[1m+++ b/src/compiler/ast_/let.py[m
[36m@@ -11,6 +11,7 @@[m [mfrom ..statement import Statement[m
 from ..scope import SisalScope[m
 from ..sub_ir import SubIr[m
 from .multi_exp import MultiExp[m
[32m+[m[32mfrom .init import Init[m
 [m
 # TODO add unwrapping the let[m
 [m
[36m@@ -31,7 +32,8 @@[m [mclass Let(Node):[m
 [m
     @build_method[m
     def build(self, target_ports: list[Port], scope: SisalScope) -> SubIr:[m
[31m-[m
         scope = SisalScope(self)[m
[32m+[m[32m        self.init = Init(self.init)[m
[32m+[m[32m        self.init.build(scope)[m
         # body = Node[m
         return SubIr([], [], [])[m
