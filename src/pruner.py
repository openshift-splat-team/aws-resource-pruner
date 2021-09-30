import boto3
from datetime import datetime, timedelta
import json

route53 = boto3.client("route53")
contextPath="/context/"
hostedZoneWithARecords="Z0109yyyyyyyyyyyyyy"
def getRecordsFromHostedZone(hostedZone):
    records = route53.list_resource_record_sets(HostedZoneId=hostedZone,MaxItems="500")
    if "ResourceRecordSets" not in records:
        print("no records found")
        return None
    
    return records["ResourceRecordSets"]

def getHostedZoneRecordState(hostedZone):
    records = getRecordsFromHostedZone(hostedZone)
    if records == None:
        return None
    recordsOfInterest = [x for x in records if "ci-op-" in x["Name"]]    

    recordNameMap = {} 
    for record in recordsOfInterest:
        recordNameMap[record["Name"]] = record
    return recordNameMap

def getHostedZoneState():
    response = route53.list_hosted_zones(MaxItems="500")

    if "HostedZones" not in response:
        print("no HostedZones received")
        return None

    hostedZones = response["HostedZones"]

    zonesOfInterest = [x for x in hostedZones if "ci-op-" in x["Name"] and (x['Name'].index("ci-op-") == 0)]    
    nameZoneMap = { }
    for zone in zonesOfInterest:
        nameZoneMap[zone["Id"]] = zone["Name"]

    return nameZoneMap

def deleteRecords(hostedZone, records, deleteSOA_NS=False):
    batch = []
    for record in records:
        type = record['Type']
        if deleteSOA_NS == False:
            if type == 'SOA' or type == 'NS':
                continue

        batch.append({
            "Action": "DELETE",
            "ResourceRecordSet": record
        })
    if len(batch) > 0:
        route53.change_resource_record_sets(HostedZoneId=hostedZone, ChangeBatch={"Changes": batch})
    return batch
    
def deleteRecordsInHostedZone(zoneId):
    records = getRecordsFromHostedZone(zoneId)
    return deleteRecords(zoneId, records)

def deleteSpecificRecordsInHostedZone(zoneId, records, deleteSOA_NS=False):        
    return deleteRecords(zoneId, records, deleteSOA_NS)

def saveStateFile(name, state):
    with open(name, "w") as stateFile:
        stateFile.write(json.dumps(state))

def loadStateFile(name):
    try:
        with open(name, "r") as stateFile:
            return json.load(stateFile)
    except:        
        return None

def getStaleHostedZones(state, savedState):
    staleHostedZones = []
    for record in state:
        if record in savedState:
            staleHostedZones.append(record)
    return staleHostedZones

def getStaleHostedZoneRecords(state, savedState):
    staleHostedZoneRecords = []
    for record in state:
        if record in savedState:
            staleHostedZoneRecords.append(savedState[record])
    return staleHostedZoneRecords

# clean up stale hosted zones
def cleanupStaleHostedZones(state, savedState):
    staleRecords = getStaleHostedZones(state, savedState)
    for record in staleRecords:
        print("delete records in hosted zone " + record)
        deletedRecords = deleteRecordsInHostedZone(record)
        print("deleted " + str(len(deletedRecords)) + " records in hosted zone ")
        if len(deletedRecords) == 0:
            print("hosted zone " + record + " is ready to be deleted")
            route53.delete_hosted_zone(Id=record)

# clean up stale records in a specific hosted zone
def cleanupStaleHostedZoneRecords(state, savedState):
    staleRecords = getStaleHostedZoneRecords(state, savedState)
    deleteSpecificRecordsInHostedZone(hostedZoneWithARecords,staleRecords, True)

def checkRunBackoff():
    then = None
    try:
        with open(contextPath+"last_run", "r") as stateFile:            
            time = stateFile.readline()
            then = datetime.strptime(time, "%d/%m/%Y %H:%M:%S\n")
    except:
        print("unable to get prior run time. ")

    now = datetime.now()
    if then == None or now > (then + timedelta(hours=5)):
        nowTime = now.strftime("%d/%m/%Y %H:%M:%S")
        with open(contextPath+"last_run", "w") as stateFile:
            stateFile.write(nowTime+"\n")
        return True
    else:
        return False


###############################################################################
if checkRunBackoff() == False:
    print("attempting to rerun too soon. try again later.")
    exit()
savedHostedZoneState = loadStateFile(contextPath+"hosted-zone-state")
savedRecordState = loadStateFile(contextPath+"hosted-zone-record-state")

hostedZoneState = getHostedZoneState()
hostedZoneRecordState = getHostedZoneRecordState(hostedZoneWithARecords)

if savedHostedZoneState != None:
    cleanupStaleHostedZones(hostedZoneState, savedHostedZoneState)

if savedRecordState != None:
    cleanupStaleHostedZoneRecords(hostedZoneRecordState, savedRecordState)

saveStateFile(contextPath+"hosted-zone-state",hostedZoneState)
saveStateFile(contextPath+"hosted-zone-record-state",hostedZoneRecordState)


