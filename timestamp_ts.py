import numpy as np
from datetime import datetime
from sgp4.api import jday

timestamp_jd = []
timestamp_fr = []
now = datetime.utcnow()
for i in range(1,181): # 1 seconds to 3 minutes away from current time
    jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second+0.000001*now.microsecond+i)
    timestamp_jd.append(jd)
    timestamp_fr.append(fr)
timestamp_jd = np.asarray(timestamp_jd)
timestamp_fr = np.asarray(timestamp_fr)

print(timestamp_jd)
print(timestamp_fr)