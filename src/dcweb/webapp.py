'''
Created on 24Feb.,2017

@author: yan073
'''

from flask import Flask
from flask import request
from flask import jsonify
from datetime import datetime

import datacube
import dcweb.status as httpstatus
import dcweb.download_util as downloadUtil
import json
from datacube.drivers.manager import DriverManager

DriverManager(default_driver_name='s3')
dc = datacube.Datacube(app='dc-example')
app = Flask(__name__)
        
@app.route("/run/<function>", methods=["GET"]) # list_products, list_variables
def run(function):
    #app.logger.error('start running method');
    if function == "list_products":        
        response = list_products()
        return jsonify(response), httpstatus.HTTP_200_OK
    elif function == "list_measurements":
        response =  list(dc.list_measurements().index) #convertDataFrame( dc.list_measurements() )
        return jsonify(response), httpstatus.HTTP_200_OK
    return "error"

def list_products():
    return convertDataFrame( dc.list_products() )

def convertDataFrame(obj):
    if obj is not None:
        str = obj.to_json(orient='records')
        return json.loads(str)
    return obj

@app.route("/get_product_info", methods=['GET'])
#http://localhost:8080/get_product_info?productname=ls5_nbar_albers
def get_product_info():
    prod_name = request.args.get('productname')
    dslist = dc.find_datasets(product=prod_name)
    
    info = {}
    if dslist:
        dstime = set([ ds.center_time for ds in dslist])
        info['time'] = [dt.strftime('%Y-%m-%dT%H:%M:%S.%f') for dt in dstime] 
        info['variables'] = list(dslist[0].measurements.keys())
        return jsonify(info), httpstatus.HTTP_200_OK   
    return jsonify(info), httpstatus.HTTP_404_NOT_FOUND

@app.route("/load_data", methods=['GET'])
#http://localhost:8228/load_data?platform=LANDSAT_5&product=ls5_nbar_albers&vars=green,red&fromtime=641949028000&totime=641949028000&northBoundLatitude=-35.28&southBoundLatitude=-35.32&eastBoundLongitude=149.18&westBoundLongitude=149.07
def load_data():
    app.logger.error('start loading dataset...');
    rawdata = load(request, request.args.get('fromtime'), request.args.get('totime') )
    response = convertDataset(rawdata) 
    return jsonify(response), httpstatus.HTTP_200_OK   

@app.route("/download_data", methods=['GET'])
#http://localhost:8080/download_data?platform=LANDSAT_5&product=ls5_nbar_albers&vars=green,red&time=641949028000&northBoundLatitude=-35.28&southBoundLatitude=-35.32&eastBoundLongitude=149.18&westBoundLongitude=149.07
def download_data():
    app.logger.error('start downloading data...');
    time = request.args.get('time')
    rawdata = load(request, time, time )
    parsed = convertDataset(rawdata)
    response = downloadUtil.convert_to_download(parsed)
    return jsonify(response), httpstatus.HTTP_200_OK

def load(request, fromtime, totime):
    platform = request.args.get('platform')
    product = request.args.get('product')
    vars = request.args.get('vars')
    northBoundLatitude = float(request.args.get('northBoundLatitude', '0'))
    southBoundLatitude = float(request.args.get('southBoundLatitude', '0'))
    eastBoundLongitude = float(request.args.get('eastBoundLongitude', '0'))
    westBoundLongitude = float(request.args.get('westBoundLongitude', '0'))
    return dc.load(product= product, 
                     platform= platform, 
                     measurements= vars.split(','), 
                     x=(westBoundLongitude, eastBoundLongitude), 
                     y=(northBoundLatitude, southBoundLatitude), 
                     time=(parseTimeQuery(fromtime), parseTimeQuery(totime)), use_threads=True)
    
def parseTimeQuery(timestr):
    return datetime.fromtimestamp( int(timestr) /1000.0) 

def convertDataset(dataset): # dataset is at type of xarray.Dataset
    interdata = {}
    interdata["attrs"] = convertDatasetAttrs(dataset.attrs)
    interdata["dimensions"] = convertDatasetFrozen(dataset.dims)
    interdata["sizes"] = convertDatasetFrozen(dataset.sizes)
    variables = convertDatasetFrozen(dataset.variables)
    interdata["dims"] = convertDatasetDims(variables)
    interdata["arrays"] = convertDatasetVariables(variables)
    interdata["indices"] = convertDatasetIndexes(dataset.indexes)
    interdata["coords"] = convertDatasetCoords(dataset.coords)    
    return convertInterDataToResponse(interdata)

def convertInterDataToResponse(interdata):
    response = interdata
    return response

def convertDatasetCoords(coords):
    # type: xarray.core.coordinates.DatasetCoordinates
    root = {}
    return root

def convertDatasetIndexes(indexes):
    root = {}
    return root

def convertDatasetDims(variables):
    # Frozen('time', 'x', 'y' ->  
    # -> xrray.IndexVariable, xrray.IndexVariable, xrray.IndexVariable
    root = {}
    srctime = variables['time'] 
    root['time'] = convertDatetime64ArrayToNanoSecondsArray(srctime.data) 
    root['x'] = variables['x'].data.tolist()
    root['y'] = variables['y'].data.tolist()
    root['attrs'] = variables['y'].attrs
    return root

def convertDatasetVariables(variables):
    # Frozen('red', 'blue', ..., ->  
    # -> xarray.Variable (3D), xarray.Variable (3D)
    root = {}
    for key in list(variables.keys()):
        if(not isCoordinate(key)):
            srcvar = variables[key] # <class 'xarray.core.variable.Variable'>
            colour = {}
            colour["values"] = srcvar.data.tolist() # <class 'numpy.ndarray'>
            colour["dims"] = srcvar.dims
            colour["attrs"] = convertXArrayAttributes(srcvar.attrs)
            root[key] = colour
    return root

def isCoordinate(key):
    return 'time' == key or 'x' == key or 'y' == key
    
def convertDatasetFrozen(frozen):
    root = {}
    for key in list(frozen.keys()):
        root[key] = frozen[key]
    return root 
    
def convertDatasetAttrs(attrs):
    root = {}
    root['crs'] = attrs['crs'].crs_str
    return root 
    
def convertDataToJson(data):
    response = {}
    response["coordinate_reference_systems"] = data["coordinate_reference_systems"]
    response["dimensions"] = data["dimensions"]
    response["size"] = data["size"]
    #response[""] = data[""]
    response["indices"] ={}
    response["indices"]["x"] = data["indices"]["x"].tolist() 
    response["indices"]["y"] = data["indices"]["y"].tolist() 
    response["indices"]["time"] = convertDatetime64ArrayToNanoSecondsArray(data["indices"]["time"])
    response["arrays"] = {} 
    arrays = data["arrays"]
    
    if arrays is not None:
        for key in arrays.keys():
            #app.logger.error(arrays[key])
            response["arrays"][key] = convertXArrayObj(arrays[key]) 
            
    response["element_sizes"] = convertElementSizes(data["element_sizes"])
    return response

def convertElementSizes(elem_sizes):
    root = []
    if elem_sizes is not None:
        index1 = 0 
        while index1 < len(elem_sizes):
            elsize = elem_sizes[index1]
            if isinstance( elsize, int ):
                root.append(elsize)
            else:
                root.append(str(elsize))
            index1 += 1
    return root

def convertXArrayObj(xrray):
    root = {}
    root["attrs"] = convertXArrayAttributes(xrray.attrs)
    root["coords"] = convertXArrayCoords(xrray.coords)
    root["dims"] = convertXArrayDims(xrray.dims)
    root["values"] = convertXArrayValues(xrray.values, xrray.ndim)
    return root

def convertXArrayCoords(coords):
    root = {}
    if coords is not None:
        # serialise "x"
        jsonx = {}
        attrs = []
        attrs.append( {"units": coords["x"].attrs["units"] } )
        jsonx["attrs"] = attrs
        jsonx["values"] = coords["x"].values.tolist()
        root["x"] = jsonx
        # serialise "y"
        jsony = {}
        attrs = []
        attrs.append( {"units": coords["y"].attrs["units"] } )
        jsony["attrs"] = attrs
        jsony["values"] = coords["y"].values.tolist()
        root["y"] = jsony
        # serialise "time"
        jsontime = {}
        attrs = []
        attrs.append( {"units": coords["time"].attrs["units"] } )
        jsontime["attrs"] = attrs
        jsontime["values"] = convertXArrayCoordsTimeDatatime64Array(coords["time"]) # [str(coords["time"].values[0])]
        root["time"] = jsontime
    return root

def convertXArrayCoordsTimeDatatime64Array(timearray):
    root =[]
    index1 = 0 
    values = timearray.values
    while index1 < len(values):
        root.append(str(values[index1]))
        index1 += 1
    return root

    
def convertXArrayDims(dims):
    root = []
    if dims is not None:
        root = list(dims)
    return root

def convert2DValues(d2value):
    root = []
    if d2value is not None:
        index1 = 0
        while index1 < len(d2value):
            jlevel1 = []
            array2 = d2value[index1]
            index2 = 0
            while index2 < len(array2):
                jlevel1.append(array2[index2].tolist())
                index2 += 1
            root.append(jlevel1)
            index1 += 1
    return root
    
    
def convertXArrayValues(values, ndim):
    root = []
    if ndim == 2: # it is a 2-D array, when there is only one sample in 'time' dimension
        root.append( convert2DValues(values) )
    elif ndim == 3: # it is a 3-D array, in the order of [time][y][x]
        index1 =0
        while index1 < len(values):
            root.append( convert2DValues(values[index1]) )
            index1 += 1
            
    return root

def convertXArrayAttributes(attrobj):
    jsonattr = {}
    jsonattr["crs"] = str(attrobj["crs"])
    jsonattr["nodata"] = attrobj["nodata"]
    jsonattr["units"] = attrobj["units"]
    jsonattr["spectral_definition"] = attrobj["spectral_definition"]
    return jsonattr
        
def  convertDatetime64ArrayToNanoSecondsArray(t64s):
    root = []
    if t64s is not None:
        rindex = 0
        while (rindex < len(t64s)):
            root.append( str(t64s[rindex]) )
            rindex += 1
    return root
  
if __name__ == '__main__':
    app.run()
