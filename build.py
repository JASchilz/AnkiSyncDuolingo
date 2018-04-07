import os
from zipfile import ZipFile


def project_files(path):

    result = []
    for root, dirs, files in os.walk(path):
        result += [os.path.join(root, f) for f in files if '.pyc' not in f]
    return result


if __name__ == '__main__':
    
    with ZipFile('duolingo_sync.zip', 'w') as myzip:
        myzip.write('duolingo_sync.py')
        myzip.write('duolingo_sync')
        myzip.write('README.md', 'duolingo_sync/README.md')
        myzip.write('LICENSE.md', 'duolingo_sync/LICENSE.md')
        
        for f in project_files('duolingo_sync'):
            myzip.write(f)



