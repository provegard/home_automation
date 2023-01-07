import aioesphomeapi
import asyncio
import collections.abc
import time
import getopt
import os
import json
import sys

# Program options, defaults
opts = {
    "logFile": "-", # stdout
    "outputFile": "-", # stdout
    "port": 6053,
    "objectIds": ["power_consumed", "power_consumed_phase_1", "power_consumed_phase_2", "power_consumed_phase_3"],
    "list": False,
    "monitorObjectId": "energy_consumed_luxembourg",
    "monitorHangLimit": 20,
}

# Shared state updated by the change_callback and read by tick.
currentState = {}

def write(fileKey, msg):
    if fileKey in opts:
        # allow date/time formatting in a filename
        filename = time.strftime(opts[fileKey], time.localtime())
        if filename == "-":
            print(msg)
        else:
            with open(filename, "a") as f:
                f.write(msg)
                f.write("\n")
    else:
        print(msg)

def log(msg):
    write("logFile", msg)

# Periodically called to write the current state as JSON
def tick():
    state = currentState.copy()
    state["seconds"] = time.time()
    stateJson = json.dumps(state)
    write("outputFile", stateJson)

# Helper function that calls the given callback on regular intervals.
def setInterval(loop, callback, interval):
    timer = None
    def wrapper():
        callback()
        timer = loop.call_later(interval, wrapper)
    timer = loop.call_later(interval, wrapper)
    return lambda: timer.cancel()
    
# Determines if x is an array
def isArray(x):
    return isinstance(x, collections.abc.Sequence) and not isinstance(x, str)

# Creates a dict that maps state key to object ID
async def createKeyLookup(api):
    entities = await api.list_entities_services()
    d = {}
    for e in entities:
        if isArray(e):
            for s in e:
                if isinstance(s, aioesphomeapi.SensorInfo):
                    d[s.key] = (s.object_id, s.unit_of_measurement)
    return d

def dumpObjectIds(lookup):
    print("Available object IDs:")
    for objId in lookup.values():
        print(f"- {objId}")

async def start(eventloop, outP):
    log(f"Establishing a connection to {opts['host']}:{opts['port']}")
    api = aioesphomeapi.APIClient(opts["host"], opts["port"], "")
    await api.connect(login=True)

    log("Mapping keys to object IDs")
    keyLookup = await createKeyLookup(api)

    if opts["list"]:
        dumpObjectIds(keyLookup)
        eventloop.stop()
        return

    monitorObjectId = opts["monitorObjectId"]
    monitorHangLimit = opts["monitorHangLimit"]
    monitorValues = []

    log(f"Monitoring {monitorObjectId} to check for hang; {monitorHangLimit} consecutive equal values will trigger a restart.")

    def check_hang(value):
        monitorValues.append(value)
        while len(monitorValues) > monitorHangLimit:
            monitorValues.pop(0)
        if len(monitorValues) == monitorHangLimit:
            allSame = len(set(monitorValues)) == 1
            if allSame:
                log(f"Hang detected! The last {monitorHangLimit} values of {monitorObjectId} are the same. Exiting with non-zero exit status to trigger systemd restart.")
                #api.disconnect() # cannot await here, not in async context
                outP["exitCode"] = 1
                eventloop.stop()
                return

    # TODO: If state doesn't change for a while, disconnect and reconnect!
    def change_callback(state):
        if state.missing_state:
            return

        if state.key in keyLookup:
            (objectId, unit) = keyLookup[state.key]

            if objectId == monitorObjectId:
                check_hang(state.state)

            if objectId in opts["objectIds"]:
                currentState[objectId] = { "value": state.state, "unit": unit }

    log("Subscribing to state changes")
    await api.subscribe_states(change_callback)

def usage():
    ids = str.join(",", opts["objectIds"])
    print(f"{sys.argv[0]} [-h][-L] [-l log file] [-o output file] <-H host name> [-p port] [-i object IDs]")
    print(f"\t-l  : path to file that will receive log messages (default {opts['logFile']})")
    print(f"\t-o  : path to file that will receive JSON output (default {opts['outputFile']})")
    print(f"\t-H  : ESPHOME host name, required")
    print(f"\t-p  : ESPHOME port (default {opts['port']})")
    print(f"\t-i  : comma-separated list of object IDs (default {ids})")
    print(f"\t-m  : object ID to monitor for hang (default {opts['monitorObjectId']})")
    print(f"\t-M  : monitor hang limit (default {opts['monitorHangLimit']})")
    print(f"\t-L  : list object IDs and exit")
    print(f"\t-h  : show this help")

def readOpts():
    optss, args = getopt.getopt(sys.argv[1:], 'H:p:l:hi:o:Lm:M:')
    for o, a in optss:
        if o == "-i":
            opts["objectIds"] = a.split(",")
        elif o == "-o":
            opts["outputFile"] = os.path.abspath(a)
        elif o == "-p":
            opts["port"] = int(a)
        elif o == "-H":
            opts["host"] = a
        elif o == "-l":
            opts["logFile"] = os.path.abspath(a)
        elif o == "-L":
            opts["list"] = True
        elif o == "-m":
            opts["monitorObjectId"] = a
        elif o == "-M":
            opts["monitorHangLimit"] = int(a)
        elif o == "-h":
            usage()
            sys.exit(2)

    if "host" not in opts:
        print("Host must be specified")
        usage()
        sys.exit(2)

def main():
    readOpts()

    log("Getting event loop")
    loop = asyncio.get_event_loop()

    log("Starting timer")
    cancelTimer = setInterval(loop, tick, 10)

    # A plain global variable didn't work.
    outP = { "exitCode": 0 }
    try:
        log("Starting up")
        asyncio.ensure_future(start(loop, outP))
        loop.run_forever()
        pass
    except KeyboardInterrupt:
        pass
    finally:
        log("Closing down")
        cancelTimer()
        #loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        log("Closed!")

        exitCode = outP["exitCode"]
        if exitCode > 0:
            sys.exit(exitCode)

if __name__ == "__main__":
    main()
