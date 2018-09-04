from celery.task import task
from subprocess import call,STDOUT
import requests, os
from requests import exceptions
from tasks import solrDeleteIndex, solrIndexSampleData, solrIndexItems
from geotransmeta import unzip,geoBoundsMetadata, determineTypeBounds
from geotransmeta import configureGeoData, crossWalkGeoBlacklight
import json

wwwdir = "/data/static"

@task()
def resetSolrIndex(items):
    """
    Delete current solr index and indexs items sent in Args
    Args:
        items (list of objects)
    returns:
        acknowledgement of workflow submitted.
        Children chain: solrDeleteIndex --> solrIndexItems
    """

    queuename = resetSolrIndex.request.delivery_info['routing_key']
    workflow = (solrDeleteIndex.si().set(queue=queuename) |
                solrIndexItems.si(items).set(queue=queuename))()
    return "Succefully Workflow Submitted: children workflow chain: solrDeleteIndex --> solrIndexItems"

@task()
def geoLibraryLoader(local_file,request_data,force=False):
    """
    Workflow to handle initial import of zipfile:
    --> Unzip
    --> Identify file type(shapefile, image, iiif)
    --> return Bounds
    --> Check for xml metadata file
    --> Initial cross walk of xml to geoblacklight schema
    Return data to applicaiton to display (Human interaction)

    Workflow is called from /upload with form that has taskname

    force (boolean): If data already uploaded will delete and replace.
    """
    task_id = str(geoLibraryLoader.request.id)
    resultDir = os.path.join(wwwdir, 'geo_tasks', task_id)
    os.makedirs(resultDir)
    if 'force' in request_data:
        force = request_data['force']
    queuename = geoLibraryLoader.request.delivery_info['routing_key']
    workflow = (unzip.s(local_file).set(queue=queuename) |
                determineTypeBounds.s().set(queue=queuename) |
                configureGeoData.s(resultDir).set(queue=queuename) |
                crossWalkGeoBlacklight.s().set(queue=queuename))()
    return "Succefully submitted geoLibrary initial workflow"
