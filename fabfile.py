from fabric.api import *
from fabric.contrib.files import exists
from contextlib import contextmanager as _contextmanager
from StringIO import StringIO

env.user = 'iweixiao'
#env.hosts = ['v2.iweixiao.cn', 'test.iweixiao.cn']
env.hosts = ['v2.iweixiao.cn']

SERVER_NAME = 'www.iweixiao.cn'
PROJECT_HOME = '/home/iweixiao/iweixiaoV2'
PROJECT_CODE = 'iwx'
GITHUB = 'https://github.com/zcmyth/iweixiaoV2.git'
VIRTUAL_ENV = '/home/iweixiao/.virtualenvs/' + PROJECT_CODE

NGINX_CONFIG=\
"""
upstream app_server {
    server 127.0.0.1:3031;
}
server {
    listen       80;
    server_name  %s;
    location /static {
        alias %s/client/static;
    }
    location / { try_files $uri @app; }
    location @app {
      include uwsgi_params;
      uwsgi_pass app_server;
    }
}
""" % (SERVER_NAME, PROJECT_HOME)

UWSGI_CONF=\
"""
start on runlevel [2345]
stop on runlevel [06]

respawn

exec uwsgi --emperor /etc/uwsgi/apps-enabled
"""

UWSGI_INI=\
"""
[uwsgi]
socket = :3031
pythonpath = {0}/server
plugins=python
module = run:app
virtualenv = {1}
daemonize = /var/log/uwsgi/{2}.log
log-format = [%(ltime)] %(addr) "%(method) %(uri)" %(status)
""".format(PROJECT_HOME, VIRTUAL_ENV, PROJECT_CODE)

TOOL_LIST = [
    'python-pip',
    'python-dev',
    'nginx',
    'uwsgi',
    'git',
    'npm',
    'node',
    'nodejs-legacy',
    'libmysqlclient-dev',
    'uwsgi-plugin-python',
    'libjpeg-dev'
]

@_contextmanager
def virtualenv():
    with cd(VIRTUAL_ENV):
        with prefix('source %s/bin/activate' % VIRTUAL_ENV):
            yield

def _puttofile(content, path):
    if exists(path, use_sudo=True):
        sudo('rm ' + path)
    put(StringIO(content), path, use_sudo=True)

def init():
    sudo('apt-get update')
    for tool in TOOL_LIST:
        sudo('apt-get install ' + tool)
    
    sudo('npm install -g grunt-cli')
    sudo('npm install -g bower')

    # install virtual env
    # http://docs.python-guide.org/en/latest/dev/virtualenvs/
    sudo('pip install virtualenv')
    sudo('pip install virtualenvwrapper')
    with prefix('source /usr/local/bin/virtualenvwrapper.sh'):
        run('mkvirtualenv ' + PROJECT_CODE)

    # init project
    if not exists(PROJECT_HOME, use_sudo=True):
        run('mkdir -p ' + PROJECT_HOME)
        with cd(PROJECT_HOME):
            run('git clone ' + GITHUB + ' .')
            with cd('client'):
                run('npm install')
                run('bower install')

    # config nginx and uwsgi
    _puttofile(NGINX_CONFIG, '/etc/nginx/sites-enabled/' + PROJECT_CODE)
    _puttofile(UWSGI_CONF, '/etc/init/uwsgi.conf')
    _puttofile(UWSGI_INI, '/etc/uwsgi/apps-enabled/%s.ini' % PROJECT_CODE)

    # install mysql-server


def deploy():
    with cd(PROJECT_HOME):
        run('git checkout master')
        run('git pull')
        with virtualenv():
            run('pip install -r %s/server/requirements.txt' % PROJECT_HOME)
        with cd('client'):
            run('grunt build')
        sudo('service uwsgi restart')


