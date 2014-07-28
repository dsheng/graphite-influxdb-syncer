import logging
import pylibmc
import time
import eventlet
from influxdb import InfluxDBClient

def config_to_client(config={}):
    
    host = config.get('host', 'localhost')
    port = config.get('port', 8086)
    user = config.get('user', 'gct')
    passw = config.get('pass', 'cloudpigct')
    db = config.get('db', 'gct')

    return InfluxDBClient(host, port, user, passw, db)

try:
    mc=pylibmc.Client(['127.0.0.1:11211'],binary=True,behaviors={'tcp_nodelay':True,'ketama':True})
except Exception,e: 
    print str(e)

mp_set = {}
def sync_serie(serie):
    key = serie['name'].encode('iso8859-1')
    #print '===>'+key
    mc_ttl = 3600 #seconds
    pn_str=''
    my_inx = 0
    #mp_set = {}
    son_tokens = key.split('.')
    for son_token in son_tokens:
        son_str = son_token
        my_inx += 1
        if my_inx < 3:
           pn_str += son_str+'.'
           continue
        mykey = pn_str + '*'
        #snstr_in_mc = mc.get(mykey)
        snstr_in_mc = mp_set.get(mykey)
        if son_token == son_tokens[-1]:
            son_str = pn_str+son_token+':1' #is a leaf
        if snstr_in_mc == None:
            #mc.set(mykey,son_str,time=mc_ttl)
            mp_set[mykey] = son_str
    	    #print mykey+'===>'+son_str
        else:
            sns_set = set(snstr_in_mc.split(','))
            if son_str not in sns_set:
                sns_set.add(son_str)
                mp_set[mykey] = ','.join(sns_set)
                #mc.set(mykey,','.join(sns_set),time=mc_ttl)
        pn_str += son_str+'.'
#    mc.set_multi(mp_set,time=mc_ttl)

class InfluxDBSyncer(object):
    __slots__ = ('client', 'logger')

    def __init__(self):
        self.client = config_to_client()
        #logging.basicConfig(filename='/tmp/graphite_influx.log',level=logging.INFO)
        logging.basicConfig()
        #self.logger = logging.getLogger("influxdbsyncer")
        #self.logger.setLevel(logging.INFO)

    def sync_series(self):
        start = time.time()
        mc.set('*','gct')
        mc.set('gct.*','counts,gauges,timers') #less than 2 will be ignore
        series = self.client.query("list series")
        print 'list====>'+str(time.time()-start)
        start = time.time()
        pool = eventlet.GreenPool(size=3000)
        for key in pool.imap(sync_serie,series):
            pass
        #for s in series:
        #     pool.spawn_n(sync_serie, s)
        #pool.waitall()
        print 'process====>'+str(time.time()-start)

if __name__ == '__main__':
    InfluxDBSyncer().sync_series()
    mc.set_multi(mp_set,time=3600)
