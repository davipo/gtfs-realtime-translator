#! /usr/local/bin/python

# getvehicles.py
# SMSMyBus-API access to GTFS-realtime data
# David "Davi" Post, DaviWorks.com
# 2014-07-11


import cgi
import cgitb
cgitb.enable()          # in development: display errors in browser when used as CGI script
# cgitb.enable(display=0, logdir='logs')    # production: log errors, don't display


import datetime
import sys
import urllib2
import json

import gtfs_realtime_pb2


expected_gtfs_rt_version = '1.0'


class GtfsRealtimeData(object):
    """ GTFS realtime data handler"""
    
    def __init__(self, feed_data, expected_feed_version=None):
        self.message = gtfs_realtime_pb2.FeedMessage()
        self.message.ParseFromString(feed_data)
        
        self.feed_time = self.message.header.timestamp          # POSIX time
            # convert with datetime.datetime.utcfromtimestamp()
        
        # Check feed version
        expected_feed_version = expected_feed_version or expected_gtfs_rt_version
        feed_version = self.message.header.gtfs_realtime_version
        if feed_version != expected_feed_version:
            print 'Feed version is %s, expecting %s\n' % (feed_version, expected_feed_version)
            ### Warning: printing this spoils JSON output
    
    def get_vehicles(self, route_id, vehicle_id=None):
        """ Return dict as specified in SMSMyBus API."""
        vpositions = self.vehicle_positions(route_id, vehicle_id)
        response = {
            'count': len(vpositions),
            'routeID': route_id,
            'timestamp': str(datetime.datetime.fromtimestamp(self.feed_time)),
            'vehicles': vpositions
        }
        if len(vpositions) > 0:
            response['status'] = '0'
        else:
            response['status'] = '-1'
            response['description'] = 'No vehicles found on route %s' % route_id
            if vehicle_id:
                response['description'] += ' with vehicle ID %s' % vehicle_id
        return response
    
    
    def vehicle_positions(self, route_id=None, vehicle_id=None):
        """ Return a list of vehicle positions, filter by route_id & vehicle_id if given.
            Each vehicle position is a dict of lat, lon, tripID, stopID, vehicleID. 
            (All data are string.)"""
        vpositions = []
        for entity in self.message.entity:
            if not entity.is_deleted:
                gtfs_vposition = entity.vehicle     # a GTFS-RT VehiclePosition
                if route_id and gtfs_vposition.trip.route_id != route_id:
                    continue
                if vehicle_id and vehicle_id != gtfs_vposition.vehicle.id:
                    continue
                vposition = {
                    'lat': gtfs_vposition.position.latitude,
                    'lon': gtfs_vposition.position.longitude,
                    'tripID': gtfs_vposition.trip.trip_id,
                    'stopID': gtfs_vposition.stop_id,
                    'vehicleID': gtfs_vposition.vehicle.id
                    }
                vpositions.append(vposition)
        return vpositions
        


def getvehicles(data_source, route_id=None, vehicle_id=None, expected_feed_version=None):
    """ Return vehicle locations as JSON, filter by route_id & vehicle_id if given. 
        If no route_id, return alphabetically sorted list of routes. 
        Data source may be a URL (begins with 'http') or a filepath. """
    opener = urllib2.urlopen if data_source.startswith('http') else open
    feed_data = opener(data_source).read()
    data = GtfsRealtimeData(feed_data, expected_feed_version)
    if route_id:
        response = data.get_vehicles(route_id, vehicle_id)
        indent = 3
    else:   # list routes if no route_id given
        routes = {entity.vehicle.trip.route_id for entity in data.message.entity 
                                               if not entity.is_deleted}
        response = {'Routes':  sorted(routes)}
        indent = None
    return json.dumps(response, indent=indent)


mtba_bus = {
    'name': 'Massachusetts Bay Transportation Authority',
    'info_url': 'http://www.mbta.com/rider_tools/developers/default.asp?id=22393',
    'feed_url': 'http://developer.mbta.com/lib/gtrtfs/Vehicles.pb',
    'feed_version': '0.1',
    'test_filename': 'Vehicles.pb'
}


if __name__ == '__main__':
    
    params = cgi.FieldStorage()
    if len(params) == 0:
        
        # Not CGI, process command-line args
        if len(sys.argv) < 2:
            response = '\n   Usage: %s <data_source> [ <route_id> [<vehicle_id>] ]\n'
            response %= sys.argv[0]
            response += '      <data_source> may be a filepath or URL\n'
            response += '      Without route_id, routes are listed\n'
        else:
            data_source, route_id, vehicle_id = (sys.argv + [None, None])[1:4]
            response = getvehicles(data_source, route_id, vehicle_id)
        print response
        
    else:
        
        # run as CGI script
        print 'Content-Type: application/json'
        print
        
        route_id = params.getfirst('routeID', None)
        vehicle_id = params.getfirst('vehicleID', None)
        data_source = mtba_bus['test_filename']
        expected_feed_version = mtba_bus['feed_version']
        response = getvehicles(data_source, route_id, vehicle_id, expected_feed_version)
        print response
    
