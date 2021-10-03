import requests
import numpy as np
import configparser
from sgp4.api import Satrec
from sgp4.api import SatrecArray
from sgp4.api import jday
from datetime import datetime

class MyError(Exception):
    def __init___(self,args):
        Exception.__init__(self,"Exception was raised with arguments {0}".format(args))
        self.args = args

# Below is the one for all debris including active satellites : This one seems better though
# https://www.space-track.org/basicspacedata/query/class/tle_latest/DECAYED/<>1/ORDINAL/<2/orderby/NORAD_CAT_ID asc/limit/90000/format/3le/

# Below is the one for non-active debris
# https://www.space-track.org/basicspacedata/query/class/tle_latest/OBJECT_TYPE/DEAD,ROCKET BODY,UNKNOWN,DEBRIS/DECAYED/<>1/ORDINAL/<2/orderby/NORAD_CAT_ID asc/limit/90000/format/3le/

uriBase = "https://www.space-track.org"
requestLogin = "/ajaxauth/login"
requestCommand = "/basicspacedata/query/class/tle_latest/DECAYED/<>1/ORDINAL/<2/orderby/NORAD_CAT_ID asc/limit/90000/format/3le/"

config = configparser.ConfigParser()
config.read("./SLTrack.ini")
configUsr = config.get("configuration","username")
configPwd = config.get("configuration","password")
configOut = config.get("configuration","output")
siteCred = {'identity': configUsr, 'password': configPwd}

# Current time matrix
timestamp_jd = []
timestamp_fr = []
now = datetime.utcnow()
for i in range(1,181): # 1 seconds to 3 minutes away from current time
    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second+0.000001*now.microsecond+i)
    timestamp_jd.append(jd)
    timestamp_fr.append(fr)
timestamp_jd = np.asarray(timestamp_jd)
timestamp_fr = np.asarray(timestamp_fr)

# use requests package to drive the RESTful session with space-track.org
download_status = False
satellites_raw = []
with requests.Session() as session:
    # run the session in a with block to force session to close if we exit

    # need to log in first. note that we get a 200 to say the web site got the data, not that we are logged in
    resp = session.post(uriBase + requestLogin, data = siteCred)
    if resp.status_code != 200:
        raise MyError(resp, "POST Request failed on logging into https://www.space-track.org")

    # this query picks up all Starlink satellites from the catalog. Note - a 401 failure shows you have bad credentials 
    resp = session.get(uriBase + requestCommand)
    if resp.status_code != 200:
        print(resp)
        raise MyError(resp, "GET Request failed on request for debris")
    else: # Successfully derived data from the server
        # Read data line by line and classify into arrays
        satellite_indv = []
        for line in resp.iter_lines():
            line = line.decode("utf-8") # Decode bytes array into string
            try:
                line_index = line[0]
            except IndexError:
                continue
            if line_index == '0': # Name
                satellite_indv.append(line[1:].strip())
            if line_index == '1': # TLE Line 1
                satellite_indv.append(line)
            if line_index == '2': # TLE Line 2
                satellite_indv.append(line)
                if len(satellite_indv) == 3:
                    satellites_raw.append(np.asarray(satellite_indv))
                # Reset the array
                satellite_indv = []
        download_status = True
        satellites_raw = np.asarray(satellites_raw)
    session.close()

if download_status == True:
    print("------------SGP4 Modeling------------")
    SatList = []
    for satellite in satellites_raw:
        print(satellite)
        name = satellite[0]
        s = satellite[1]
        t = satellite[2]
        SatList.append(Satrec.twoline2rv(s, t))
    a = SatrecArray(np.asarray(SatList))
    # Update Model
    e, r, v = a.sgp4(timestamp_jd, timestamp_fr)
    print("================Current Position================")
    print(r)
    print("================Current Velocity================")
    print(v)

else:
    print("Something went wrong while parsing data from space-track.org")