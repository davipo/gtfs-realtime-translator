## gtfs-realtime-translator
Translate GTFS-realtime data feed

Reads a General Transit Feed Specification realtime feed, recoding to JSON format. Used to provide realtime bus locations to apps for bus riders.

### Files
    Vehicles.pb             
        Sample GTFS-realtime bus locations data for demo 
        (Google protocol buffer format)

    gtfs-realtime.proto
        GTFS-realtime protocol buffer specification

    gtfs_realtime_pb2.py
        Python module to read protocol buffer data format
        (generated from above with Google's protocol buffer compiler)

    getvehicles.py
        Script to translate GTFS-realtime feed to JSON format

