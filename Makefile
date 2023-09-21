bug1:
	roslaunch bug_alg bug1.launch des_x:=6 des_y:=6

bug2:
	roslaunch bug_alg bug2.launch des_x:=-1.1 des_y:=-1.1

class1:
	roslaunch bug_alg class1.launch des_x:=2 des_y:=-1

class11:
	roslaunch bug_alg class11.launch des_x:=3 des_y:=4

distbug:
	roslaunch bug_alg distbug.launch des_x:=3 des_y:=0

distbug_step:
	roslaunch bug_alg distbug_step.launch des_x:=3 des_y:=0

rules:
	chmod +x src/bug_alg/CMakeLists.txt
	chmod +x src/bug_alg/package.xml
	chmod +x src/bug_alg/setup.py
	chmod +x src/bug_alg/launch/*.launch
	chmod +x src/bug_alg/scripts/*.py
	chmod +x src/bug_alg/src/bug_alg/__init__.py