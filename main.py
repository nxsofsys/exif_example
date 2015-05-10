# coding=utf-8
import logging
import sys
import signal
from app import App
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import define, options
import socket
import os
import __builtin__

define("port", default=8000, help="run on the given port", type=int)
define("host", default=socket.getfqdn(), help="host name")

def main():
    options.parse_command_line()
    __builtin__.app = App()
    server = HTTPServer(app,
        max_buffer_size = 32*1024*1024, xheaders=True)
    port = options.port
    server.listen(port)
    print 'Listening on port %i'%port
    def shutdown():
        print 'Shutdown called...'
        server.stop()
        io_loop = IOLoop.instance()
        def stop_callbacks():
            if io_loop._callbacks:
                print 'Processing current connections...'
                io_loop.call_later(1, stop_callbacks)
            else:
                print 'All done - shutdown!'
                io_loop.stop()
        stop_callbacks()
    signal.signal(signal.SIGINT, 
        lambda sig, frame: IOLoop.instance().add_callback_from_signal(shutdown))
    IOLoop.instance().start()


if __name__ == "__main__":
    main()
