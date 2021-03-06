from abc import ABCMeta, abstractmethod
import sys, os

class Data(metaclass=ABCMeta):
    filepath = None
    _info = None
    def __init__(self, filepath):
        self.filepath = filepath;
        self.parse()
    def __str__(self):
        return self.symbol()+self._info['type']+','+self._info['data']
    @abstractmethod
    def parse(self):
        pass
    def info(self):
        return self._info
    def __str__(self):
        str = ('-'*100)+'\n'
        str += self._info['type']+'\t'+self._info['name']+'\n'+self._info['data']+'\n\n'
        return str

class ObjectData(Data):
    def parse(self):
        _fileinfo = os.path.split(self.filepath)
        object = _fileinfo[0][-2:] + _fileinfo[1]
        path = self.filepath[:-55]
        try:
            import subprocess
            p = subprocess.Popen("cd "+path+";git cat-file -p "+object, shell=True, stdout=subprocess.PIPE)
            data = p.communicate()[0].decode('utf-8').strip()
            p = subprocess.Popen("cd "+path+";git cat-file -t "+object, shell=True, stdout=subprocess.PIPE)
            t = p.communicate()[0].decode('utf-8').strip()
        except UnicodeDecodeError as e:
            data = "Can't parsing"
            t = 'unknown'
        self._info = {
            'type' : t,
            'name' : object,
            'data' : data,
            'path' : self.filepath
        }
    def __str__(self):
        content = self._info['data']
        if self._info['type'] == 'blob':
            content = content[:100]
        str = '________________________________________________\n'
        str += self._info['type']+'\t'+self._info['name']+'\n'+content+"\n\n"
        # str += '________________________________________________\n'
        return str


class ObjectDataById(ObjectData):
    def __init__(self, object_id, path):
        self.object = object_id
        self.filepath = '.git/objects/'+object_id[0:2]+'/'+object_id[2:]
        self.path = path
        self.parse()
    def parse(self):
        object = self.object
        try:
            import subprocess
            p = subprocess.Popen("cd "+self.path+";git cat-file -p "+object, shell=True, stdout=subprocess.PIPE)
            data = p.communicate()[0].decode('utf-8').strip()
            p = subprocess.Popen("cd "+self.path+";git cat-file -t "+object, shell=True, stdout=subprocess.PIPE)
            t = p.communicate()[0].decode('utf-8').strip()
        except UnicodeDecodeError as e:
            data = "Can't parsing"
            t = 'unknown'
        self._info = {
            'type' : t,
            'name' : object,
            'data' : data,
            'path' : self.filepath
        }

class TextData(Data):
    def parse(self):
        content = open(self.filepath, 'rb').read()
        self._info = {
            'type' : 'REFE',
            'name' : self.filepath,
            'data' : content.decode('utf-8'),
            'path' : self.filepath
        }

class IndexData(Data):
    def parse(self):
        import subprocess
        p = subprocess.Popen("cd "+self.filepath.replace('/index','')+";git ls-files --stage", shell=True, stdout=subprocess.PIPE)
        data = p.communicate()[0].decode('utf-8').strip()
        self._info = {
            'type' : 'index',
            'name' : 'index',
            'data' : data,
            'path' : self.filepath,
            'mtime' : os.path.getmtime(self.filepath)
        }

class PackData(Data):
    def parse(self):
        import subprocess
        p = subprocess.Popen("git verify-pack -v "+self.filepath, shell=True, stdout=subprocess.PIPE)
        data = p.communicate()[0].decode('utf-8').strip()
        self._info = {
            'type' : 'pack',
            'name' : self.filepath,
            'data' : data,
            'path' : self.filepath
        }

class UnknonData(Data):
    def parse(self):
        try:
            content = open(self.filepath, 'rb').read().decode('utf-8')
        except UnicodeDecodeError as e:
            content = "Can't parse"
        self._info = {
            'type' : 'unknown',
            'name' : self.filepath,
            'data' : content,
            'path' : self.filepath
        }

class GitDataObjectFactory:
    @staticmethod
    def getElement(path):
        path = path.replace('\\', '/')
        if not os.path.isfile(path):
            return None
        if '.git/objects/pack' in path:
            return PackData(path)
        if '.git/objects/info' in path:
            return TextData(path)
        elif '.git/objects' in path:
            return ObjectData(path)
        elif '.git/index' in path:
            return IndexData(path)
        return UnknonData(path)

class GitElement:
    path = None
    def __init__(self, path):
        self.path = path
    @staticmethod
    def getFileRecursivly(path, _reverse=True):
        import sys, os, operator
        fileList = []
        for (_path, _dir, _files) in os.walk(path):
            _path = _path.replace('\\', '/')
            for _file in _files:
                fpath = os.path.join(_path,_file)
                mtime = os.path.getmtime(fpath);
                fileList.append([fpath, mtime])
        fileList.sort(key=operator.itemgetter(1), reverse=_reverse)
        return fileList
    def getAll(self):
        elist = []
        for item in GitElement.getFileRecursivly('.git'):
            elist.append(GitDataObjectFactory.getElement(item[0]))
        return elist;
