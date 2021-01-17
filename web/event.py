from flask import Blueprint, render_template
from flask import current_app as app

from pathlib import Path
import time
import random

from core import api
from plugins.event.models import event

pluginPages = Blueprint('eventPages', __name__, template_folder="templates")

@pluginPages.route("/event/")
def mainPage():
    findActiveEvents = event._event().getAsClass(sessionData=api.g.sessionData,query={"expiryTime" : { "$gt" : time.time() } })
    return render_template("event.html", events=findActiveEvents)

@pluginPages.route("/event/<eventID>/")
def getEvent(eventID):
    foundEvent = event._event().query(sessionData=api.g.sessionData,id=eventID)["results"][0]
    return foundEvent, 200

@pluginPages.route("/event/eventCorrelation/<eventCorrelationID>/")
def eventCorrelationPage(eventCorrelationID):
    return render_template("eventCorrelation.html")


@pluginPages.route("/event/eventCorrelation/<eventCorrelationID>/get/")
def getEventCorrelation(eventCorrelationID):
    eventCorrelation = event._eventCorrelation().getAsClass(sessionData=api.g.sessionData,id=eventCorrelationID)[0]
    nodes = {}
    edges = []
    timeMap = []
    for sourceEvent in eventCorrelation.events:
        if sourceEvent["eventRaiseTime"] not in timeMap:
            timeMap.append(sourceEvent["eventRaiseTime"])
        if sourceEvent["uid"] not in nodes:
            nodes[sourceEvent["uid"]] = { "_id" : sourceEvent["_id"], "eventTime" : sourceEvent["eventRaiseTime"], "eventValues" : [] }
            for field, fieldValue in sourceEvent["eventValues"].items():
                nodes[sourceEvent["uid"]]["eventValues"].append([field,fieldValue])
        else:
            if sourceEvent["eventRaiseTime"] < nodes[sourceEvent["uid"]]["eventTime"]:
                nodes[sourceEvent["uid"]]["eventTime"] = sourceEvent["eventRaiseTime"]
                nodes[sourceEvent["uid"]]["_id"] = sourceEvent["_id"]
                for field, fieldValue in sourceEvent["eventValues"].items():
                    if [field,fieldValue] not in nodes[sourceEvent["uid"]]["eventValues"]:
                        nodes[sourceEvent["uid"]]["eventValues"].append([field,fieldValue])

    for sourceEvent, targetEvent in ((sourceEvent, targetEvent) for sourceEvent in eventCorrelation.events for targetEvent in eventCorrelation.events):
        if sourceEvent["uid"] != targetEvent["uid"]:
            temp = { "source" : sourceEvent["uid"], "target" : targetEvent["uid"], "matches" : [ ] }
            for field, fieldValue in sourceEvent["eventValues"].items():
                if type(fieldValue) is list:
                    for fieldValueItems in fieldValue:
                        try:
                            if type(targetEvent["eventValues"][field]) is list:
                                if fieldValueItems in targetEvent["eventValues"][field]:
                                    temp["matches"].append([field,fieldValueItems])
                            else:
                                if fieldValueItems == targetEvent["eventValues"][field]:
                                    temp["matches"].append([field,fieldValueItems])
                        except KeyError:
                            pass
                try:
                    if type(targetEvent["eventValues"][field]) is list:
                        if fieldValue in targetEvent["eventValues"][field]:
                            temp["matches"].append([field,fieldValue])
                    else:
                        if fieldValue == targetEvent["eventValues"][field]:
                            temp["matches"].append([field,fieldValue])
                except KeyError:
                    pass
            if len(temp["matches"]) > 0:
                edges.append(temp)

    timeMap.sort()
    for key, item in nodes.items():
        item["x"] = timeMap.index(item["eventTime"])*500
        item["y"] = round(random.random()*50*len(nodes))

    return { "nodes" : nodes, "edges" : edges }, 200




