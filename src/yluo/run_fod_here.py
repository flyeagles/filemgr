import os

from sys import executable
from subprocess import Popen, CREATE_NEW_CONSOLE

if __name__ == "__main__":

    target_cfg_file = 'originaldb.cfg'

    if os.path.exists(target_cfg_file):
        print("WARNING: Config file {cfg} exists. SQLite DB file will be overwritten!".format(cfg=target_cfg_file))

    Popen([executable, 'clip_monitor_ws.py'], creationflags=CREATE_NEW_CONSOLE)
    Popen([executable, 'monitor_file_change.py'], creationflags=CREATE_NEW_CONSOLE)

    os.system("python manage.py runserver")
