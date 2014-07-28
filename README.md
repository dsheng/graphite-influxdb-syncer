Graphite-InfluxDB-Syncer
=======================

This project is modified from Graphite-InfluxDB
(https://github.com/vimeo/graphite-influxdb)
and add memcache to cache InfluxDB series

Installation
------------

::

    pip install graphite_influxdb

    yum remove libmemcached libmemcached-devel
    wget https://launchpad.net/libmemcached/1.0/1.0.18/+download/libmemcached-1.0.18.tar.gz
    tar zxvf ...configure...make install
    vi /etc/ld.so.conf add /usr/local/lib
    ldconfig -v |grep libmemcached
    pip install pylibmc

    Then replace graphite_influxdb.py file in python library path from this project

    run sync_influxdb.py to sync all series to memcache 

Using with graphite-api
-----------------------

In your graphite-api config file::

    finders:
      - graphite_influxdb.InfluxdbFinder
    influxdb:
       host: localhost
       port: 8086
       user: user name
       pass: user password
       db:   db name

Using with graphite-web
-----------------------

In graphite's ``local_settings.py``::

    STORAGE_FINDERS = (
        'graphite_influxdb.InfluxdbFinder',
    )
    INFLUXDB_HOST = "localhost"
    INFLUXDB_PORT = 8086
    INFLUXDB_USER = "user name"
    INFLUXDB_PASS = "user password"
    INFLUXDB_DB =  "db name"

