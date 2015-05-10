import redis
import tornado.web
from tornadotools.route import Route
from hashlib import md5
from datetime import datetime
import cPickle
import os.path
from shared import ImageDesc
from tornado.escape import url_escape

class App(tornado.web.Application):
    def __init__(self):
        handlers = Route.routes()
        settings = dict(
            debug = True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.mc = redis.StrictRedis()

@Route('/')
class MainHandler(tornado.web.RequestHandler):
    _error = ''

    @property
    def error(self):
        return self.get_argument('error', self._error)

    @error.setter
    def error(self, value):
        self._error = value

    def get(self):
        desc_list = []
        try:
            self.page = 1
            try:
                self.page = int(self.get_argument('page'))
            except:
                pass
            size = 100
            end = size * self.page
            start = end - size
            hash_values = app.mc.lrange('_images', start, end)
            if len(hash_values) > 100:
                hash_values = hash_values[:-1]
                have_more = True
            else:
                have_more = False
            desc_list = app.mc.mget(hash_values) if hash_values else []
            desc_list = [cPickle.loads(v) for v in desc_list]
        except Exception as e:
            self.error = str(e)
            raise
        self.render('templates/main.html',
            desc_list = desc_list, have_more = have_more)

    def post(self):
        try:
            act = self.get_argument('act')
            if act == 'Delete':   
                hash_value = self.get_argument('hash_value')
                app.mc.lrem('_images', 1, hash_value) 
                os.remove(os.path.join('static', hash_value+'.jpg')) 
                os.remove(os.path.join('static', hash_value+'_thumb.jpg')) 
                app.mc.delete(hash_value)
                self.redirect('/')
            else:
                fileinfo = self.request.files['file'][0]
                data = fileinfo['body']
                fname = fileinfo['filename']
                ext = os.path.splitext(fname)[1]
                hash_value = md5(data).hexdigest()
                now = datetime.now()
                now_string = now.strftime('%Y:%m:%d %H:%M:%S')
                desc = cPickle.dumps(ImageDesc(
                    hash_value = hash_value
                    , ext = ext
                    , name = self.get_argument('name').encode('utf-8')
                    , upload_date = now_string
                    , creation_date = None
                    , camera = None
                    , size = None
                    , status = 'Pending'))

                res = app.mc.setnx(hash_value, desc)
                if res == 0:
                    raise Exception("Image exists")
                with open(os.path.join('upload', hash_value+'.' + ext), 'wb') as f:
                    f.write(data)
                app.mc.lpush('_incoming', hash_value) 
                self.redirect('/status/'+hash_value)
        except Exception as e:
            self.error = str(e)
            self.redirect('/?error='+ \
                url_escape(self.error)+'&page='+self.get_argument('page', '1'))

@Route('/status/([a-fA-F\d]{32})')
class StatusHandler(tornado.web.RequestHandler):
    def get(self, hash_value):
        desc = app.mc.get(hash_value)
        if not desc:
            status = 'Not found'
        else:
            desc = cPickle.loads(desc) 
            status = desc.status
        self.render('templates/status.html',
            status = status, hash_value = hash_value) 