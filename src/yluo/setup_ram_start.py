import os
import shutil
import argparse

from sys import executable
from subprocess import Popen, CREATE_NEW_CONSOLE

if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description='Set up execution at RAMDisk.')
    argparser.add_argument("--RAM", dest='RAM_disk', # metavar='Folder-root',
                           type=str, default=None, required=True,
                           help='root of the RAM disk')
    argparser.add_argument("--force", dest='force_copy', # metavar='Folder-root',
                           default=False, required=False, action='store_true',
                           help='whether to force copy files to RAM disk')

    args = argparser.parse_args()

    # print(args.accumulate(args.folder_root))
    curpath = os.getcwd()

    target_folder = os.path.join(args.RAM_disk, '\\', os.path.basename(curpath))
    print(target_folder)

    try:
        shutil.copytree('.', target_folder)
        print("Copy all contents from {cur} to {target}".format(cur=curpath, target=target_folder))
    except FileExistsError as err:
        if args.force_copy:
            shutil.rmtree(target_folder)
            shutil.copytree('.', target_folder)
        else:
            print(err)
            print("Cannot create new target folder. Will just re-use existing content.")

    target_cfg_file = os.path.join(target_folder, 'originaldb.cfg')
    FILE = open(target_cfg_file, 'w')
    FILE.write('origin='+curpath)
    FILE.close()
    print("Write config to " + target_cfg_file)

    os.chdir(target_folder)

    Popen([executable, 'clip_monitor_ws.py'], creationflags=CREATE_NEW_CONSOLE)
    Popen([executable, 'monitor_file_change.py'], creationflags=CREATE_NEW_CONSOLE)

    os.system("python manage.py runserver")
