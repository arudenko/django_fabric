django_fabric
============
1. Just wanted to create simple [Fabric](http://docs.fabfile.org/en/1.6/) configuration to:
	- Install:
		- nginx
		- mysql
		- uwsgi
	- make all this work together 
	- have django skeleton for quick projects

2. It works from virtual environment
	- To Setup virtual environment:
		- `python bootstrap.py djn_env`;
		- Setup environment in PyCharm:
			- Preferences - > Project Settings -> Python Interpreter
			- Click "Add"
			- Select tts_env/bin/Python
		- to upgrade environment run `python bootstrap.py djn_env` one more time

3. [Vagrant](http://www.vagrantup.com)
	Project has simple [Vagrant](http://www.vagrantup.com) file to test local instances. To spead up development it maps host folders to cache apt and virtualenv files. 

4. To run
	1. Access Test Data:
	    - login: root
	    - password: 123