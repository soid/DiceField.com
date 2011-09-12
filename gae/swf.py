from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import time
import random

# SWF loader. This prevents appengine's traffic quota overuse.
# see the thread: http://groups.google.com/group/google-appengine/browse_thread/thread/7c6a42f0c6f92423/69e6a641ebe2b1aa


last_req = 0 # instance cache
last_ips = []
delays = {}
block_list = []

class StaticPage(webapp.RequestHandler):
    def get(self):
        global last_req, last_ips, delays
        
        delay = time.time() - last_req
        last_req = time.time()

        if (delay < 1) and (self.request.remote_addr in block_list):
            # too little delay between requests from the same IP
            self.error(503)
            return

        if delay < 0.5:
            if self.request.remote_addr in last_ips:
                if (time.time() - delays[self.request.remote_addr]) < 2:
                    del delays[self.request.remote_addr]
                    last_ips.remove(self.request.remote_addr)
                    block_list.append(self.request.remote_addr)
                    if len(block_list) > 10:
                        block_list.pop(0)
                    return
                else:
                    delays[self.request.remote_addr] = last_req
            elif random.randint(0, 5) == 1:
                last_ips.append(self.request.remote_addr)
                delays[self.request.remote_addr] = last_req
                if len(last_ips) > 20:
                    l = last_ips.pop(0)
                    del delays[l]

        # allright, give the file
        f = open('static/game.swf', 'r')    
        if f:
            self.response.headers['Content-Type'] = 'application/x-shockwave-flash'
            self.response.out.write(f.read())
        else:
            self.response.out.write("Not found")

application = webapp.WSGIApplication(
        [
            (r'/.*', StaticPage),
        ],
        debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
