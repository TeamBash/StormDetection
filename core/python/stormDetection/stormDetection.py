import json
import logging
import random
import requests
import uuid
from datetime import datetime

from flask import Flask
from kazoo.client import KazooClient
from kazoo.client import KazooState
from kazoo.exceptions import KazooException

app = Flask(__name__)


@app.route('/getKml/noaa-nexrad-level2.s3.amazonaws.com/<yy>/<mm>/<dd>/<stationId>/<filename>.gz', methods=['GET'])
def stormDetection(yy=None, mm=None, dd=None, stationId=None, filename=None):
    if yy and mm and dd and stationId and filename:
        url = 'https://noaa-nexrad-level2.s3.amazonaws.com/' + yy + '/' + mm + '/' + dd + '/' + stationId + '/' + filename + '.gz'
        result = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>KML Samples</name>
    <Folder>
      <name>Ground Overlays</name>
      <visibility>0</visibility>
      <description>Examples of ground overlays</description>
      <GroundOverlay>
        <name>Large-scale overlay on terrain</name>
        <visibility>0</visibility>
        <description>Overlay shows Mount Etna erupting on July 13th, 2001.</description>
        <LookAt>
          <longitude>15.02468937557116</longitude>
          <latitude>37.67395167941667</latitude>
          <altitude>0</altitude>
          <heading>-16.5581842842829</heading>
          <tilt>58.31228652890705</tilt>
          <range>30350.36838438907</range>
        </LookAt>
        <Icon>
          <href>http://developers.google.com/kml/documentation/images/etna.jpg</href>
        </Icon>
        <LatLonBox>
          <north>37.91904192681665</north>
          <south>37.46543388598137</south>
          <east>15.35832653742206</east>
          <west>14.60128369746704</west>
          <rotation>-0.1556640799496235</rotation>
        </LatLonBox>
      </GroundOverlay>
    </Folder>
  </Document>
</kml>
'''
        return result, 200

def getValue(sId, ec2IP, path):
    return json.dumps({"name": "stormDetection",
                       "id": sId,
                       "address": ec2IP,
                       "port": 34000,
                       "sslPort": None,
                       "payload": None,
                       "registrationTimeUTC": (datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds(),
                       "serviceType": "DYNAMIC",
                       "uriSpec": {"parts": [{"value": path,
                                              "variable": True}]}}, ensure_ascii=True).encode()


def my_listener(state):
    global ip
    if state == KazooState.LOST:
        zkIP = ip + ":2181"
        zk = KazooClient(hosts=zkIP)
        zk.start()
    elif state == KazooState.SUSPENDED:
        print("Connection Suspended")
    else:
        print("Connection Error")


def register():
    try:
        global ip
        sId = str(uuid.uuid4())
        zkIp = ip + ":2181"
        zk = KazooClient(hosts=zkIp)
        zk.start()
        zk.add_listener(my_listener)
        path = "http://" + ip + ":34000/getKml/"
        zk.create("/services/stormDetection/" + sId, getValue(sId, ip, path), ephemeral=True, makepath=True)
    except KazooException as e:
        print(e.__doc__)
    logging.basicConfig()


if __name__ == '__main__':
    ip = requests.get("http://checkip.amazonaws.com/").text.split("\n")[0]
    #ip = "127.0.0.1"
    register()
    app.run(
        host="0.0.0.0",
        port=int(34000)
        # debug=True
    )
