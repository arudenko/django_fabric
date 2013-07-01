import virtualenv
s = virtualenv.create_bootstrap_script('''
import subprocess
def after_install(options, home_dir):
    if sys.platform == 'win32':
        bin = 'Scripts'
    else:
        bin = 'bin'
    pip = os.path.join(home_dir, bin, 'pip')
    subprocess.call([pip, 'install', '-r', 'requirements.txt'])
''')
open('bootstrap.py','w').write(s)