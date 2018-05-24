import os
import re

def get_original_folder():
    originalfile = None
    cfgfilename = '.\\originaldb.cfg'
    if os.path.exists(cfgfilename):
        FILE = open(cfgfilename, 'r')
        for line in FILE:
            print(line)
            if 'origin=' in line:
                match = re.search('=(.*?)$', string=line)
                if match:
                    originalfile = match.group(1)
        FILE.close()
    
    return originalfile
