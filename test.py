#coding=utf8
import urllib2
import sys
import Queue
import threading
import json
import os
import copy
max_thread = 10

def PrintMessage(msg):
    print >> sys.stderr, '\r',
    print >> sys.stderr, msg,


def DownloadFile(url,tofile):
    r = urllib2.urlopen(url)
    fileSize=int(r.headers.dict['content-length'])
    outf = open(tofile, 'wb')
    c = 0

    while True:
        s = r.read(1024 * 32)
        if len(s) == 0:
            break
        outf.write(s)
        c += len(s)
        PrintMessage('Download %s (%d/%d)' % (url,c,fileSize))
    outf.close()

max_thread = 10
# 初始化锁
lock = threading.RLock()
class mainQueue():
    waiting = Queue.Queue()
    completed = Queue.Queue()
    taskFile = ""
    def __init__(self,taskFile):
        self.taskFile = taskFile
        if os.path.exists(taskFile) and os.path.isfile(taskFile):
            f=open(taskFile,"r")
            tFile = f.read()
            jsonObject=json.loads(tFile)
            for (key,value) in jsonObject.items():
                if key == "0":
                    for i in value:
                        self.waiting.put(i)
                if key == "1":
                    for i in value:
                        self.completed.put(i)
    def save(self):
        jsonDict = {}
        tQueue = copy.deepcopy(self.waiting)
        taskList = []
        while not tQueue.empty():
            taskList.append(tQueue.get())
        jsonDict["0"]=taskList
        taskList = []
        tQueue = copy.deepcopy(self.completed)
        while not tQueue.empty():
            taskList.append(tQueue.get())
        jsonDict["1"]=taskList
        f = open(self.taskFile,"w")
        d = json.dumps(jsonDict)
        f.write(d)
        f.close()


class Downloader(threading.Thread):
    aSize = None

    def __init__(self, url, start_size, end_size, fobj, buffer,t_size=None):
        self.url = url
        self.buffer = buffer
        self.start_size = start_size
        self.end_size = end_size
        self.fobj = fobj

        self.aSize = t_size
        threading.Thread.__init__(self)
    def run(self):
        """
            马甲而已
        """
        #with lock:
            # print 'starting: %s' % self.getName()
        self._download()
    def _download(self):
        """
            我才是搬砖的
        """
        req = urllib2.Request(self.url)
        # 添加HTTP Header(RANGE)设置下载数据的范围
        req.headers['Range'] = 'bytes=%s-%s' % (self.start_size, self.end_size)
        f = urllib2.urlopen(req)
        # 初始化当前线程文件对象偏移量
        offset = self.start_size
        while 1:
            block = f.read(self.buffer)
            # 当前线程数据获取完毕后则退出
            if not block:
                #with lock:
                #   print '%s done.' % self.getName()
                break
            # 写如数据的时候当然要锁住线程
            # 使用 with lock 替代传统的 lock.acquire().....lock.release()
            # 需要python >= 2.5
            with lock:
            #    sys.stdout.write('%s saveing block...' % self.getName())
                # 设置文件对象偏移地址
                self.fobj.seek(offset)
                # 写入获取到的数据
                self.fobj.write(block)

                offset = offset + len(block)
            #    sys.stdout.write('done.\n')
                #
                if self.aSize!=None:
                    self.aSize.completedSize += len(block)
                    PrintMessage('%.2fMB / %.2fMB' % (
                    float(self.aSize.completedSize) / (1024.0 * 1024.0), float(self.aSize.allSize) / (1024.0 * 1024.0)))

def main(url, thread=3, save_file='', buffer=1024*1024,completeAction = None):
    # 最大线程数量不能超过max_thread
    thread = thread if thread <= max_thread else max_thread
    # 获取文件的大小
    print('startDownload %s'%(url))
    req = urllib2.urlopen(url)
    size = int(req.info().getheaders('Content-Length')[0])
    # 初始化文件对象
    fobj = open(save_file, 'wb')
    # 根据线程数量计算 每个线程负责的http Range 大小
    avg_size, pad_size = divmod(size, thread)
    aSize = sizeMode(size)
    plist = []
    for i in xrange(thread):
        start_size = i*avg_size
        end_size = start_size + avg_size - 1
        if i == thread - 1:
            # 最后一个线程加上pad_size
            end_size = end_size + pad_size + 1
        t = Downloader(url, start_size, end_size, fobj, buffer,aSize)
        plist.append(t)
    #  开始搬砖
    for t in plist:
        t.start()
    # 等待所有线程结束
    for t in plist:
        t.join()
    # 结束当然记得关闭文件对象
    fobj.close()
    if completeAction!=None:
        completeAction()

def buildTask(taskFile):
    f = open(taskFile,'w')
    oF = open('\users\test.txt','r')
    lines =oF.readlines()
    oF.close()
    taskList = []
    for line in lines:
        taskList.append(unicode(line.replace('\r\n',''),errors='ignore'))
    taskJson ={'0':taskList,'1':[]}
    d=json.dumps(taskJson)
    f.write(d)
    f.close()
totalCount = 0
if __name__ == '__main__':
    hasTaskList = True
    que=mainQueue("/Users/nts001/Documents/tumblr/taskList.txt")
    que.save()
    '''
    for line in lines:
        url =line
        fileName ="/Users/nts001/Documents/tumblr/%s"%(url.split('/')[-1])
        main(url,thread=10,save_file=fileName,buffer=1024)
    '''
