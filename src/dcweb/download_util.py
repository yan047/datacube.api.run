
def convert_to_download(parsed):
    response = {}
    response['size'] = get_size(parsed)
    response['indices'] = get_indices(parsed)
    # there is no 'element_sizes' in parsed or raw!
    response['dimensions'] = get_dimensions(parsed)
    response['coordinate_reference_systems'] = get_crs(parsed)
    response['arrays'] = get_data(parsed)
    return response
    
def get_size(parsed):
    root = []
    root.append(parsed['sizes']['time'])
    root.append(parsed['sizes']['y'])
    root.append(parsed['sizes']['x'])
    return root

def get_dimensions(parsed):
    return ['time', 'y', 'x']

def get_indices(parsed):
    return parsed['dims']

def get_crs(parsed):
    # there is no "coordinate_reference_systems" in the parsed, only crs: "EPSG:3577"
    root = []
    rcd = {}
    rcd["reference_system_definition"] = parsed['attrs']['crs']
    rcd["reference_system_unit"] = parsed['dims']['attrs']['units']
    root.append(rcd)
    return root
    
def get_data(parsed):
    root = parsed['arrays']
    coords = get_coords(parsed)
    for key in root.keys():
        colour = root[key]
        colour["coords"] = coords
    return root
    
def get_coords(parsed):
    root = {}
    time = {}
    time["values"] = parsed['dims']["time"]
    xycoordattrs = get_xy_coords_attrs(parsed)
    x = {}
    x["values"] = parsed['dims']["x"]
    x["attrs"] = xycoordattrs
    y = {}
    y["values"] = parsed['dims']["y"]
    y["attrs"] = xycoordattrs
    root["time"] = time
    root["x"] = x
    root["y"] = y
    return root

def get_xy_coords_attrs(parsed):
    root = []
    root.append(parsed['dims']['attrs'])
    return root