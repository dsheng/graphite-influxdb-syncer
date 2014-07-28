import re
import logging
import pylibmc
import time
import traceback
import os

try:
    from graphite_api.intervals import Interval, IntervalSet
    from graphite_api.node import LeafNode, BranchNode
except ImportError:
    from graphite.intervals import Interval, IntervalSet
    from graphite.node import LeafNode, BranchNode

from influxdb import InfluxDBClient

def config_to_client(config=None):
    if config is not None:
        cfg = config.get('influxdb', {})
        host = cfg.get('host', 'localhost')
        port = cfg.get('port', 8086)
        user = cfg.get('user', 'graphite')
        passw = cfg.get('pass', 'graphite')
        db = cfg.get('db', 'graphite')
    else:
        from django.conf import settings
        host = getattr(settings, 'INFLUXDB_HOST', 'localhost')
        port = getattr(settings, 'INFLUXDB_PORT', 8086)
        user = getattr(settings, 'INFLUXDB_USER', 'graphite')
        passw = getattr(settings, 'INFLUXDB_PASS', 'graphite')
        db = getattr(settings, 'INFLUXDB_DB', 'graphite')

    return InfluxDBClient(host, port, user, passw, db)


class InfluxDBReader(object):
    __slots__ = ('client', 'path', 'logger')

    def __init__(self, client, path, logger):
        self.client = client
        self.path = path
        self.logger = logger

    def fetch(self, start_time, end_time):
        step = 1
        data = self.client.query("select time, value from %s where time > %ds and time < %ds order asc" % (self.path, start_time-step, end_time+step))
        datapoints = []
        start = 0
        end = 0
        try:
            points = data[0]['points']
            start = points[0][0]
            end = points[-1][0]
            #step = points[1][0] - start
            step = end - points[-2][0]
            datapoints = [p[2] for p in points]
        except Exception:
            pass
        if len(datapoints)==0:
            datapoints = []

        time_info = start-step, end+step, step
        return time_info, datapoints

    def get_intervals(self):
        last_data = self.client.query("select * from %s limit 1" % self.path)
        first_data = self.client.query("select * from %s limit 1 order asc" % self.path)
        last = 0
        first = 0
        try:
            last = last_data[0]['points'][0][0]
            first = first_data[0]['points'][0][0]
        except Exception:
            pass
        return IntervalSet([Interval(first, last)],126)

class InfluxdbFinder(object):
    __slots__ = ('client', 'logger','mc')

    def __init__(self, config=None):
        self.client = config_to_client(config)
        # from graphite_api.app import app
        # self.logger = app.logger
        #logging.basicConfig()
        logging.basicConfig(filename='/tmp/graphite_influx_syner.log')
        self.logger = logging.getLogger("graphite-influxdb-syner")
        self.logger.setLevel(logging.INFO)
        try:
	    self.mc=pylibmc.Client(['127.0.0.1:11211'],binary=True,behaviors={'tcp_nodelay':True,'ketama':True})
        except Exception,e: 
            self.logger.error(str(e))

    def find_nodes(self, query):
        qstr = str(query.pattern).encode('iso8859-1')
        if qstr == None:
            qstr = '*'
        if(qstr.endswith("*") == False):
            yield LeafNode(qstr, InfluxDBReader(self.client, qstr , self.logger))
            return

        son_nodes_str = self.mc.get(qstr)
        #self.logger.info('find_nodes son_nodes_str:===>'+son_nodes_str)

        if son_nodes_str != None:
            son_nodes = son_nodes_str.split(',')
            for node in son_nodes:
                if node.endswith(':1'):
                    yield LeafNode(node[:-2], InfluxDBReader(self.client, node[:-2] , self.logger))
                else:
                    yield BranchNode(node)
        return;
