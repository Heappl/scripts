import re


def extract(msgName, msgContent):
    #return msgName + ":" + msgContent
    return msgName
    if (msgName == "IMUpdateNotification") or (msgName == "IMExecutionRequest"):
        res = re.findall('distname:="([^"]+TRU_L[^"]+)"', msgContent)
        if (not res):
            return msgName
        return msgName + "(" + ",".join(res) + ")"
        #res = re.search('.*', msgContent)
        #res = re.search('.*distname:="([^"]+)"', msgContent)
        return msgName if (res == None) else msgName + "(" + res.group(1) + ")"

    if (msgName == "IMChangeRequest"):
        res = re.search('request_id:=([^,]+).*distname:="([^"]+TRU_L[^"]+)"', msgContent)
        #res = re.search('request_id:=([^,]+).*distname:="([^"]+)"', msgContent)
        #return msgName if (res == None) else msgName + "#" + res.group(1) + "(" + res.group(2) + ")"
        return msgName if (res == None) else msgName + "(" + res.group(2) + ")"
        
        #res = re.search("object:=.*object:={([^:]+):=", msgContent)
        #return msgName if (res == None) else msgName + "(" + res.group(1) + ")"

    #if (msgName == "IMOperationExecuted"):
        #res = re.search('request_id:=([^,]+)', msgContent)
        #return msgName if (res == None) else msgName + "#" + res.group(1)

    if (msgName == "IMExecutionResult"):
        res = re.search('request_id:=([^,]+).*execution_status:=([^,}]+)', msgContent)
        #return msgName if (res == None) else msgName + "#" + res.group(1) + "(" + res.group(2) + ")"
        return msgName if (res == None) else msgName + "(" + res.group(2) + ")"
    return msgName

