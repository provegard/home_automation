import os
from datetime import datetime
import json

def readLastLine(filepath):
    with open(filepath, "rb") as f:
        try:  # catch OSError in case of a one line file 
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        return f.readline().decode()

def lineToJson(csvLine):
    parts = csvLine.split(";")
    time = float(parts[0])

    # uptime is not reliable:
    # 1665206751.75;32767;217;126;491;496;401;-512;228;-512;0;0;0;0;0;0;0;1;1;0;0;202;217;232;247;495;520;545;207;232;257;330;120;0;0;0;0;0
    # 1665206811.77;-<F8>;217;126;491;496;401;-512;228;-512;0;0;0;0;0;0;0;1;1;0;0;202;217;232;247;495;520;545;207;232;257;330;120;0;0;0;0;0
    # 1665206871.8;-32767;216;126;491;495;401;-512;228;-512;0;0;0;0;0;1;0;1;1;0;0;202;217;232;247;495;520;545;207;232;257;330;120;0;0;0;0;0
    #uptime_minutes = int(parts[1])
    
    gt1 = int(parts[2]) / 10.0    # framledningstemp
    gt2 = int(parts[3]) / 10.0    # utetemp
    gt3_1 = int(parts[4]) / 10.0  # tappvarmvatten
    gt3_2 = int(parts[5]) / 10.0  # varmvatten
    gt3_3 = int(parts[6]) / 10.0  # varmevatten = golvslingor
    gt6 = int(parts[8]) / 10.0    # hetgastemp / kompressor
    b5 = bool(int(parts[14]))     # kompressor
    b8 = bool(int(parts[17]))     # circulationspump
    b9 = bool(int(parts[18]))     # flakt
    b10 = bool(int(parts[19]))    # larm
    
    est_temp = int(parts[23]) / 10.0  # beraknad temperatur

    elec_sum = int(parts[34]) / 10.0    # el-tillskott (VV + RAD)
    elec_rad = int(parts[36]) / 10.0
    elec_vv = int(parts[37]) / 10.0

    elec_kw = 9.0
    est_kw = 9.0 * elec_sum / 100.0

    fan_kw = 0.165
    comp_kw = 0.5

    current_fan_kw = fan_kw if b9 else 0.0
    current_comp_kw = comp_kw if b5 else 0.0

    total_kw = est_kw + current_fan_kw + current_comp_kw

    data = {
        "time": time,
        "temperatures": {
            "gt1": gt1,
            "gt2": gt2,
            "gt3_1": gt3_1,
            "gt3_2": gt3_2,
            "gt3_3": gt3_3,
            "gt6": gt6,
            "outdoor": gt2,
            "floor_water": gt1,
            "faucet_water": gt3_1,
            "compressor": gt6,
            "estimated": est_temp
        },
        "flags": {
            "b5": b5,
            "b8": b8,
            "b9": b9,
            "b10": b10,
            "compressor": b5,
            "circulation_pump": b8,
            "fan": b9,
            "alarm": b10
        },
        "power_draw": {
            "sum_pct": elec_sum,
            "rad_pct": elec_rad,
            "vv_pct": elec_vv,
            "est_kw": est_kw,
            "fan_kw": current_fan_kw,
            "compressor_kw": current_comp_kw,
            "total_kw": total_kw
        }
    }

    return json.dumps(data, indent=4)

def latestLineAsJson(basepath):
    filepath = basepath + "/" + datetime.now().strftime("%Y%m%d") + ".dat"
    csvLine = readLastLine(filepath)
    return lineToJson(csvLine)

if __name__ == "__main__":
    print(latestLineAsJson("/media/passport/dump/ivt490"))

