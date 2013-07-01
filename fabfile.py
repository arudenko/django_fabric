from contextlib import contextmanager
from datetime import datetime
import fnmatch
import os
import time
from time import gmtime, strftime
import fabric
from fabric.api import *
from fabtools import require
import fabtools
from fabtools.require.python import virtualenv
from fabtools.vagrant import vagrant
from fabric.contrib.files import upload_template, exists

# root
env.root = env.root = os.path.abspath(os.path.dirname(__file__)) + "/"

print env.root

# project
env.project_name = 'django_server'
env.django_project_dir = 'django_server'

# paths
# > remote
env.path = '/var/www/apps/%(project_name)s' % env
env.env_path = '%(path)s/env' % env
env.repo_path = '%(path)s/repo' % env
env.rel_path = '%(path)s/rel' % env
env.curr_path = '%(path)s/current' % env

env.pip_req_file = '%(repo_path)s/requirements.txt' % env

# > local
env.maintenance_file = '%(root)s/deploy/etc/maintenance.html.tmpl' % env

# config
env.activate = 'source %(env_path)s/bin/activate' % env
env.python = 'python2.7'
env.utc_ts = gmtime()
env.utc_ts_str = strftime('%Y%m%d_%H%M%S', env.utc_ts)
env.settings = 'vagrant'

# DB
env.db_name = "django_db"
env.db_user = "dbuser"
env.db_password = "somerandomstring"
env.db_root_password = 's3cr3t_androotpassword'


@task
def staging():
    env.settings = 'production'
    env.user = "root"
    env.hosts = ['localhost']


def setup_directories():
    require.directory('%(path)s' % env, owner="www-data", use_sudo=True)
    require.directory('%(repo_path)s' % env, owner="www-data", use_sudo=True)
    require.directory('%(rel_path)s' % env, owner="www-data", use_sudo=True)


def upload_local_folder():
    with lcd(env.root):
        local("tar cfz /tmp/release-bundle.tgz " + "./*")

    sudo('rm -rf %(repo_path)s/*' % env)
    put("/tmp/release-bundle.tgz", "%(repo_path)s" % env, use_sudo=True)

    with cd('%(repo_path)s' % env):
        sudo("tar xf release-bundle.tgz")

    put(env.root + "requirements.txt", env.repo_path, use_sudo=True)
    require.directory('%(repo_path)s/static' % env, owner="www-data", use_sudo=True)

def configure_app():
    context = {
        'db_name': env.db_name,
        'db_user': env.db_user,
        'db_password': env.db_password,
    }

    upload_template("etc/local_settings.py.in",
                    '/var/www/apps/%(project_name)s/repo/django_fabric/local_settings.py' % env,
                    context=context, use_sudo=True)


def symlink_release():
    """ Symlink the current release """
    """ See: http://blog.moertel.com/articles/2005/08/22/how-to-change-symlinks-atomically """
    milliseconds_since_epoch = int(round(time.time() * 1000))
    curr_tmp = '%s_%s' % (env.curr_path, milliseconds_since_epoch)

    sudo('ln -s %s %s && mv -Tf %s %s' %
         (get_latest_release(),
          curr_tmp,
          curr_tmp,
          '%(curr_path)s' % env))



def get_sorted_releases():
    """ Returns the list of releases sorted """
    with cd('%(rel_path)s' % env):
        return sorted(sudo('ls -xt').split())


def get_latest_release():
    releases = get_sorted_releases()
    return '%s/%s' % (env.rel_path, releases[-1])


def remove_latest_release():
    latest_release = get_latest_release()
    with cd('%(rel_path)s' % env):
        sudo('rm -rf %s' % latest_release)


def keep_num_releases(num_releases):
    releases = get_sorted_releases()
    num_to_delete = len(releases) - num_releases

    # Must keep a minimum of one release
    if num_to_delete > 1:
        del_releases = releases[:num_to_delete]
        with cd('%(rel_path)s' % env):
            for release in del_releases:
                sudo('rm -rf %s' % release)


def find_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                yield os.path.join(root, basename)


@task
def configure_uwsgi(conf_file):
    """ Configure UWSGI app server"""
    #require('settings', provided_by=[production, staging, local])
    context = {
        'django_project_dir': env.django_project_dir,
        'project_name': env.project_name,
        'python_path': env.env_path + "/lib/python2.7/site-packages",
    }

    upload_template(conf_file,
                    '/etc/uwsgi/apps-available/%(project_name)s' % env,
                    context=context,
                    use_sudo=True)

    sudo('ln -fs /etc/uwsgi/apps-available/%(project_name)s /etc/uwsgi/apps-enabled/%(project_name)s.xml' % env)
    app('restart')


@task
def configure_www(conf_file):
    """ Configure the Nginx www server"""
    #    require('settings', provided_by=[production, staging, local])
    context = {
        'server_name': env.project_name,
        'curr_path': env.curr_path,
    }
    upload_template(conf_file,
                    '/etc/nginx/nginx.conf',
                    context=context, use_sudo=True)

    www('restart')


@contextmanager
def virtualenv_created():
    with cd(env.env_path):
        with prefix(env.activate):
            yield


def setup_virtualenv():
    if not exists('%(env_path)s/bin' % env):
        sudo('virtualenv -p %(python)s --no-site-packages %(env_path)s;' % env)
        with virtualenv_created():
            sudo('easy_install -U setuptools')
            sudo('easy_install pip')


def copy_to_releases():
    sudo('cp -R %(repo_path)s %(rel_path)s/%(utc_ts_str)s' % env)
    sudo('rm -rf %(rel_path)s/%(utc_ts_str)s/.git*' % env)


def install_requirements():
    """ Install pip requirements.txt """
    # TODO This is not working
    with virtualenv():
        sudo('pip install -r {pip_req_file:s}'.format(env))


@task
def deploy(update_requirements=False):
    """ Checkout, configure, symlink release """

    upload_local_folder()
    configure_app()
    copy_to_releases()

    if update_requirements:
        install_requirements()

    symlink_release()
    manage("collectstatic --noinput")
    sudo("sudo chown -R www-data /var/www/apps/%(django_project_dir)s/current/static/" % env)

    app('restart')


def mysql_execute(sql, user='', password=''):
    """
    Executes passed sql command using mysql shell.
    """
    run("echo '%s' | mysql -u%s -p%s" % (sql, user, password))


@task
def reset_db():
    # TODO Add backup
    with settings(mysql_user='root', mysql_password=env.db_root_password):
        if fabtools.mysql.database_exists(env.db_name):
            mysql_execute('DROP DATABASE %s;' % env.db_name, "root", env.db_root_password)

    mysql_create_db()
    manage("syncdb --noinput --no-initial-data")
    manage("loaddata test.json --ignorenonexistent")
    pass


def mysql_create_db():
    with settings(mysql_user='root', mysql_password=env.db_root_password):
        require.mysql.user(env.db_user, env.db_password)
        require.mysql.database(env.db_name, owner=env.db_user)

def mysql_dump():
    """ Runs mysqldump. Result is stored at /srv/active/sql/ """

    dump_dir = '/srv/active/sql/'
    run('mkdir -p %s' % dump_dir)
    now = datetime.now().strftime("%Y.%m.%d-%H.%M")

    with settings(mysql_user='root', mysql_password=env.db_root_password):
        if fabtools.mysql.database_exists(env.db_name):
            mysql_execute('DROP DATABASE %s;' % env.db_name, "root", env.db_root_password)


    fabric.api.run('mysqldump -u%s -p %s > %s' % (user, database,
                                                  os.path.join(dump_dir, '%s-%s.sql' % (database, now))))



@task
def setup():
    if not exists('%(env_path)s/bin' % env): # this si just to run it only once
        sudo("apt-get update")
        if env.settings != "vagrant":
            sudo("apt-get upgrade -y")

    # Require some Debian/Ubuntu packages
    require.deb.packages([
        'mc',
        'vim',
        'uwsgi',
        'uwsgi-plugin-python',
        'python-virtualenv',
        'python-setuptools',
        'libmysqlclient-dev',
    ])

    setup_directories()
    upload_local_folder()

    require.mysql.server(password=env.db_root_password)

    setup_virtualenv()

    with fabtools.python.virtualenv('%(env_path)s' % env):
        require.python.package('distribute')
        fabtools.require.python.requirements('%(pip_req_file)s' % env, use_sudo=True, user="root",
                                             download_cache="/opt/r3/django/venv_cache")


    # TODO Do we need this simple webserver?
    CONFIG_TPL = '''
    server {
        listen      %(port)d;
        server_name %(server_name)s %(server_alias)s;
        root        %(docroot)s;
        access_log  /var/log/nginx/%(server_name)s.log;
    }'''

    require.nginx.site('example.com', template_contents=CONFIG_TPL,
                       port=80,
                       server_alias='www.example.com',
                       docroot='/var/www/mysite',
    )

    configure_www("etc/nginx.conf.in")

    deploy()

    configure_uwsgi("etc/uwsgi.conf.in")
    reset_db()


def service(name, *actions):
    """ Generic service function """
    for action in actions:
        sudo('/etc/init.d/%s %s' % (name, action))


@task
def app(action):
    service('uwsgi', action)


@task
@roles('www')
def www(action):
    service('nginx', action)


@task
@roles('www')
def manage(command, path=env.curr_path):
    with virtualenv_created():
        with cd(path):
            sudo('python manage.py %s' % (command,))

