# -*- coding: utf-8 -*-

# extractMesh(inputFile[, objFile][, keywordArg1...])
#   Extract mesh from .dae.phyre file and convert to obj format
#   If objFile is not specified, the data is processed but not written out
#   See meshArgs0 below for the various optiona keyword arguments that
#   can be specified. Note that most are for debugging purposes and should not
#   be needed.
#
# extractDDS(inputFile, objFile[, keywordArg1...])
#   Extract DDS file from a .dds.phyre file and convert to .dds format.
#   See ddsArgs0 below for optional keyword arguments. 


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

import os
import struct

# global variable names with default values
meshArgs0={
   'faceHeaderAddr': 0x0, # Starting address to search for face header
   'faceStartAddr': 0x0, # Starting address to search for face definitions 
   'vertStartAddr': None, # Address of first vertex block (None=find automatically)
   'vertHeaderAddr': 0x0, # Starting address to search for vertex header
   'includeNormals': False,  # Include face normals
   'invertVertUV': True, # Invert vertical coordinate of UV maps
   'maxVert': 1.e3, # Warning if any vertices exceed max
   'uvBounds': (-.01, 1.01), # Warn if any UV coordinates outside bounds
   'normTol': 1.e-6, # Warn if normals aren't within norm tolerance
   'debug': False, # Debugging output (messy)
   'showWarn': True,  #Turn off warnings about expected values
   'maxWarns': 25 # maximum number of warnings per function call
}

ddsArgs0={'ddsStartAddr': None, # Start address for DDS data (None=find automatically)
         'width': None, # Forced width resolution (None=find automatically)
         'height': None, # Forced height resolution (None=find automatically)
         'encode': None, # DXT1/DXT3/DXT5/ARGB8, (None=find automatically)
         'mipMaps': None  # Number of mip maps in file (None=find automatically)
        }

        
meshArgs = []
ddsArgs = []

# Data to search for to find start of face index list
# Cannot be called as a keyword argument!
firstFace = struct.pack('3H', 0, 1, 2) # search for 0, 1, 2 as first face

encode0={'DXT5':  {'bbp':  8, 'minDim': 4}, \
        'DXT3':  {'bbp':  8, 'minDim': 4}, \
        'DXT1':  {'bbp':  4, 'minDim':  4}, \
        'ARGB8': {'bbp': 32, 'minDim':  1} \
       }

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# Generic functions
def parseKeywords(options0, kwargs):
    # Parse provided keyword arguments, and fill in defaults to dict
    
    options = options0.copy()
    for key, val in kwargs.items():
        options[key] = val
    return options

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# extractMesh functions

def extractMesh(inputFile, objFile=None, **kwargs):
    # Primary driver for extracting mesh

    global meshArgs
    meshArgs = parseKeywords(meshArgs0, kwargs)
    
    print("EXTRACTMESH")
    
    print("Reading phyre file %s..." % inputFile)
    with open(inputFile,'rb') as file:
        f = file.read()
    
    print("Extracting faces...")
    faceSet = extractFaceSets(f)
    if not faceSet:
        raise Exception("Faces could not be found")
    
    if meshArgs['debug']: print("Number of sets: %d" % len(faceSet))
    
    if meshArgs['vertStartAddr'] is None:
        nbyte = faceSet[-1]['nFace']*2*3
        meshArgs['vertStartAddr'] = faceSet[-1]['addr'] + nbyte
        if meshArgs['debug']: 
            print("Computed start address of vertices: " + hex(meshArgs['vertStartAddr']))
    else:
        print("User-supplied start address of vertices: " + hex(meshArgs['vertStartAddr']))
    
    print("Finding vertex block addresses...")
    vertBlockAddr = findVertAddresses(f, faceSet)
    if vertBlockAddr is None:
        raise Exception("Vertex addresses could not be found")
        
    print("Extracting vertices...")
    vertSet = extractVertSets(f, faceSet, vertBlockAddr)
    
    print("Extracting UV maps...")
    uvSet = extractUvSets(f, faceSet, vertBlockAddr)

    if meshArgs['includeNormals']:
        print("Extracting normals...")
        normSet = extractNormSets(f, faceSet, vertBlockAddr)
    else:
        normSet = None
        print("Ignoring normals")    
        
    if objFile is not None:
        print("Writing object file to %s..." % objFile)
        writeObjFile(objFile, faceSet, vertSet, uvSet, normSet)
    
    print("Summary:")
    print("  Total Sets:     %d" % len(faceSet))
    print("  Total Faces:    %d" % sum(n['nFace'] for n in faceSet))
    print("  Total vertices: %d" % sum(n['nVert'] for n in faceSet))
    print("  ----------------------------------------------------------------------")
    print("  | ID | Faces | Verts | Face Addr | Vert Addr |   UV Addr | Norm Addr |")
    print("  ----------------------------------------------------------------------")
    for i in range(len(faceSet)):
        if meshArgs['includeNormals']:
            normAddr=hex(normSet[i]['addr'])
        else:
            normAddr=""
        if uvSet is None:
            uvAddr=""
        else:
            uvAddr=hex(uvSet[i]['addr'])
        print("  | %2d | %5d | %5d | %9s | %9s | %9s | %9s |" % \
          (i,  faceSet[i]['nFace'], faceSet[i]['nVert'], \
           hex(faceSet[i]['addr']), hex(vertSet[i]['addr']), \
           uvAddr, normAddr))
    print("  ----------------------------------------------------------------------")
    
#------------------------------------------------------------------------------
def extractFaceSets(f):    
    # Extract face sets by looking up header info
    
    faceSet = []

    print("  Finding start of face header blocks...")
    match = meshArgs['faceHeaderAddr']
    faceHeaderCatch=b'\xff\xff\xff\xff'
    match = f.find(faceHeaderCatch, match+1) 
    while match > 0:
        block = struct.unpack_from('27I', f, match)
        nFace = block[13]/3
        nVert = block[12]+1
        
        valid = True
        if nFace % 1 > 0: valid = False 
        if nFace <= 0: valid = False
        if nFace > 0xffff: valid = False # needs to fit in uint16
        if nVert < 3: valid = False  # always at least 3 vertices
        if nVert >= 0xffff: valid = False # needs to fit in uint16
        if block[22] != 0: valid = False # face block offset (0 for first block)
        if block[24] != nFace*2*3: valid = False # number of bytes in face block
        
        if valid:
            break
        else:
            match = f.find(faceHeaderCatch, match+1)
            
    pos = match
    if match < 0:
        print("    FAIL: Couldn't find face header block")
        return None
    if meshArgs['debug']: print("    Start of face header blocks: " + hex(pos))
    block = struct.unpack_from('27I', f, pos)
    iset = 0
    nFace = 0
    faceAddr = 0
    print("  Processing face header blocks...")
    while block[0] == 0xffffffff:
        
        # word-align for iset>0
        if iset>0 and (nFace%2) == 1:
            faceAddr += 2
        
        nFace = int(block[13]/3)
        nVert = block[12]+1
        if nFace <= 0 or nFace > 0xffff or nVert < 3 or nVert > 0xffff:
            print("    FAIL: Unexpected number of faces (%d) or verts (%d) for set %d" % (nFace, nVert, iset))
            return None
            
        # Find initial face address
        if iset == 0:
            print("    Finding face start address...")
            faceAddr = findFaceStartAddr(f, nFace, nVert)
            if faceAddr is None:
                print("      FAIL: Could not find face start address")
                return None
        
        faceSet.append({'addr': faceAddr, \
                        'faces': [], \
                        'nFace': nFace, \
                        'nVert': nVert})
       
        if meshArgs['debug']:
            print("    Face ID: %2d Address: %10s  #Faces: %5d  #Verts: %5d" % (iset, hex(faceAddr), nFace, nVert))
        
        # Grab faces
        posFace = faceSet[iset]['addr']
        for i in range(nFace):
            face = struct.unpack_from('3H', f, posFace)
            if max(face) + 1 > nVert:
                print("    FAIL: Could not read faces, vertex index (%d) higher than expected max (%d) on set %d" % (max(face)+1, nVert, len(faceSet)-1))
                return None
            elif i==0 and face != (0, 1, 2):
                print("    WARN: Expected start of faces to be (0,1,2), instead received (%d, %d, %d) for set %d" % (face[0], face[1], face[2],  i))
            faceSet[iset]['faces'].append(face)
            posFace += 6
        maxVert = max(max(x) for x in faceSet[iset]['faces'])+1
        if maxVert < nVert:
            print("    WARN: Max vert index (%d) less than nVert (%d) for set %d" % (maxVert, nVert, iset))
            
        faceAddr += 2*3*nFace
        pos += 27*4
        iset += 1
        block = struct.unpack_from('27I', f, pos)
    if not faceSet:
        print("    FAIL: Could not read face header block")
        return None
    return faceSet
        
    
def findFaceStartAddr(f, nFace, nVert):
    
    pos0 = meshArgs['faceStartAddr']
    match = f.find(firstFace, pos0)
    while match >= 0:
        if meshArgs['debug']:
            print("      Possible face start address: " + hex(match))
        pos = match
        iFail = False
        imax = 0
        for i in range(nFace):
            face = struct.unpack_from('3H', f, pos)
            if max(face) + 1 > nVert or max(face) > imax + 3:
                if meshArgs['debug']:
                    print("        Face values (face=%d, max=%d, prevMax=%d, nVert=%d) not consistent at address. Continuing search..." % (i, max(face), imax, nVert))
                iFail = True
                break;
            imax = max(imax, max(face))
            pos += 6
        if iFail:
            pos0 = pos
            match = f.find(firstFace, pos0)
        else:
            if meshArgs['debug']:
                print("      Found face start address: " + hex(match))
            return match
    return None

#------------------------------------------------------------------------------
def findVertAddresses(f, faceSet):
    # Required for the few files that don't have the same number of floats per 
    # vertex in the vertex block data. Seems to work for everything
    
    headerCatch=struct.pack('2I', 12, int(faceSet[0]['nVert']))  
    print("  Finding start of vertex header blocks...")
    offset = meshArgs['vertHeaderAddr']
    match = f.find(headerCatch, offset)
    while match >= 0:
        block = struct.unpack_from('16I', f, match)
        if block[14] == faceSet[0]['nVert']*4*3:
            break;
        match = f.find(headerCatch, match+1)
    if match < 0:
        print("    FAIL: Could not find start of header info")
        return None
    pos = match
    if meshArgs['debug']: print("    Start of header info: " + hex(pos))

    addr = [meshArgs['vertStartAddr']]
    iset = 0
    s = 0 # current position relative to last set address
    print("  Processing vertex header blocks...")
    while iset <= len(faceSet)-1: 
        pos0 = pos
        # Check for equally sized sets
        imult = 1
        while (iset + imult) < len(faceSet) and faceSet[iset]['nVert'] == faceSet[iset+imult]['nVert']:
            imult += 1
        if meshArgs['debug'] and imult > 1:
            print("    Sets %d-%d have same # verticies. Assuming equal split" % (iset, iset+imult-1))
        (pos, s) = getHeaderBlockSize(f, pos, faceSet[iset]['nVert'])
        if s == 0:
            print("    FAIL: Could not read header info for set %d" % iset)
            return None
        s = int(s/imult)
        for i in range(imult):
            addr.append(addr[-1] + s)
            if meshArgs['debug']:
                print("    Set %d has %d floats per vertex (header info starts at %s)" \
                      % (iset, s/4/faceSet[iset]['nVert'], hex(pos0)))
            iset += 1
    return addr
    
#------------------------------------------------------------------------------
def getHeaderBlockSize(f, pos, nVert):
    
    vertSize = 0
    info = struct.unpack_from('16I', f, pos)
    if info[0] != 12:
        return (pos, vertSize)
    while info[1] == nVert:
        pos += 16*4
        vertSize += info[0]*info[1] # bytes of total vertex block
        info = struct.unpack_from('16I', f, pos)
    return (pos, vertSize)
    
#------------------------------------------------------------------------------    
def extractVertSets(f, faceSet, vertBlockAddr):
    # Pull vertex data
    
    vertSet = []
    iWarn = 0
    for iset in range(len(faceSet)):
        nVert = faceSet[iset]['nVert']
        pos = vertBlockAddr[iset]
        vertSet.append({'addr': pos, 'nVert': nVert, 'verts': []})
        if meshArgs['debug']: 
            print("  Vert set %2d at %s" % (iset, hex(vertSet[iset]['addr'])))
        for iv in range(nVert):
            vert = struct.unpack_from('3f', f, pos)
            if meshArgs['showWarn'] and (max(map(abs,vert)) > meshArgs['maxVert']):
                iWarn += 1
                if iWarn <= meshArgs['maxWarns']:
                    print("  WARN: Vertex %d in set %d has large values! " \
                          % (iv, iset) + "(%.8f %.8f %.8f)" % vert)
                elif iWarn == meshArgs['maxWarns'] + 1:
                    print("  Additional warnings suppressed")
            vertSet[iset]['verts'].append(vert)
            pos += 3*4
    return vertSet

#------------------------------------------------------------------------------    
def extractUvSets(f, faceSet, vertBlockAddr):
    # Pull UV data
    
    uvSet = []
    iWarn = 0
    
    # Check if there's room for UV maps in first set 
    nVert = faceSet[0]['nVert']
    if len(faceSet) == 1:
        nfpv = int((len(f)-1 - vertBlockAddr[0])/4/nVert)
    else:
        nfpv = (vertBlockAddr[1] - vertBlockAddr[0])/4/nVert
    if nfpv < 8:
        if  meshArgs['showWarn']:
            print("  NOTE: UV maps not present (%f floats per vert). Does a texture file exist?" % nfpv)
        return None
        
    for iset in range(len(faceSet)):
        nVert = faceSet[iset]['nVert']
        pos = vertBlockAddr[iset] + (3+3)*4*nVert
        uvSet.append({'addr': pos, 'nVert': nVert, 'uvs': []})
        if meshArgs['debug']: 
            print("  UV set %2d at %s" % (iset, hex(uvSet[iset]['addr'])))
        for iv in range(nVert):
            uv = struct.unpack_from('2f', f, pos)
            if meshArgs['showWarn'] and \
            (max(uv) > meshArgs['uvBounds'][1] or min(uv) < meshArgs['uvBounds'][0]):
                iWarn += 1
                if iWarn <= meshArgs['maxWarns']:
                    print("  WARN: UV map %d in set %d is out of expected bounds! "\
                          % (iv, iset) + "(%.8f %.8f)" % uv)
                elif iWarn == meshArgs['maxWarns'] + 1:
                    print("  Additional warnings suppressed")
            uvSet[iset]['uvs'].append(uv)
            pos += 2*4
    if meshArgs['invertVertUV']:
        print("  Inverting vertical component of UV maps...")
        invertUv(uvSet)
    return uvSet

#------------------------------------------------------------------------------
def extractNormSets(f, faceSet, vertBlockAddr):
    # Pull normals data
    
    normSet = []
    iWarn = 0
    for iset in range(len(faceSet)):
        nVert = faceSet[iset]['nVert']
        pos = vertBlockAddr[iset] + nVert*4*(3)
        normSet.append({'addr': pos, 'nVert': nVert, 'norms': []})
        if meshArgs['debug']: 
            print("  Normals set %2d at %s" % (iset, hex(normSet[iset]['addr'])))
        for iv in range(nVert):
            nrm = struct.unpack_from('3f', f, pos)
            if meshArgs['showWarn'] and (abs(l2Norm(nrm)-1.0) > meshArgs['normTol']):
                iWarn += 1
                if iWarn <= meshArgs['maxWarns']:
                    print("  WARN: Norm %d in set %d is outside tolerance! "\
                          %(iv, iset) + "(%.8f)" % l2Norm(nrm))
                elif iWarn == meshArgs['maxWarns'] + 1:
                    print("  Additional warnings suppressed")
            normSet[iset]['norms'].append(nrm)
            pos +=3*4
    return normSet

#------------------------------------------------------------------------------        
def invertUv(uvSet):
    # Invert UV map
    
    for iset in range(len(uvSet)):
        for iv in range(uvSet[iset]['nVert']):
            uvSet[iset]['uvs'][iv] = (uvSet[iset]['uvs'][iv][0], \
                                      1.0 - uvSet[iset]['uvs'][iv][1])

#------------------------------------------------------------------------------
def l2Norm(x):
    # Simple L2 norm
    
    return  sum(y**2 for y in x)**.5 

#------------------------------------------------------------------------------
def writeObjFile(objFile, faceSet, vertSet, uvSet, normSet=None):
    # Write the .obj file  
    
    file = open(objFile, 'w')
    
    file.write("# %s\n" % os.path.basename(objFile))
    file.write("# Total vertices: %d\n" % sum(face['nVert'] for face in faceSet))
    file.write("# Total faces: %d\n" % sum(face['nFace'] for face in faceSet))
    
    file.write("#\n# Vertices\n")
    for iset in range(len(vertSet)):
        if iset == 0:
            faceSet[0]['offset'] = 1
        else:
            faceSet[iset]['offset'] = faceSet[iset-1]['offset'] + faceSet[iset-1]['nVert']
        file.write("# Starting Address: %s (%d vertices)\n" \
                   % (hex(vertSet[iset]['addr']), vertSet[iset]['nVert']))
        for iv in range(vertSet[iset]['nVert']):
            file.write("v %.8e %.8e %.8e\n" % vertSet[iset]['verts'][iv])
    
    if uvSet is not None:
        file.write("#\n# UV Maps\n")
        for iset in range(len(uvSet)):
            file.write("# Starting Address: %s (%d UV vertices)\n" \
                       % (hex(uvSet[iset]['addr']), uvSet[iset]['nVert']))
            for iv in range(uvSet[iset]['nVert']):
                file.write("vt %.8e %.8e\n" % uvSet[iset]['uvs'][iv])
            
    if normSet is not None:
        file.write("#\n# Normals\n")
        for iset in range(len(normSet)):
            file.write("# Starting Adress: %s (%d normals)\n" \
                       % (hex(normSet[iset]['addr']), normSet[iset]['nVert']))
            for iv in range(normSet[iset]['nVert']):
                file.write("vn %.8e %.8e %.8e\n" % normSet[iset]['norms'][iv])
        
    file.write("#\n# Face indices\n")
    for iset in range(len(faceSet)):
        file.write("# Starting Address: %s (%d faces, %d vertices)\n" \
                   % (hex(faceSet[iset]['addr']), faceSet[iset]['nFace'], \
                      faceSet[iset]['nVert']))
        file.write("g %s\n" % ("obj_" + str(iset)))
        offset = faceSet[iset]['offset']
        for i in range(faceSet[iset]['nFace']):
            face = faceSet[iset]['faces'][i]
            face = tuple(j+offset for j in face)
            if uvSet is not None and normSet is None:
                file.write("f %d/%d %d/%d %d/%d\n" % \
                           (face[0], face[0], \
                            face[1],face[1], \
                            face[2], face[2]))
            elif uvSet is None and normSet is not None:
                file.write("f %d//%d %d//%d %d//%d\n" % \
                           (face[0], face[0], \
                            face[1],face[1], \
                            face[2], face[2]))
            elif uvSet is None and normSet is None:
                file.write("f %d %d %d\n" % (face[0], face[1], face[2]))
            else:
                file.write("f %d/%d/%d %d/%d/%d %d/%d/%d\n" % \
                           (face[0], face[0], face[0], \
                            face[1], face[1], face[1], \
                            face[2], face[2], face[2]))
    file.close()
    
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# DDS functions

def extractDDS(phyreFile, ddsFile, **kwargs):
    # Main driver for DDS file extraction
    
    global ddsArgs, encode
    
    ddsArgs = parseKeywords(ddsArgs0, kwargs)
    
    print("EXTRACTDDS")
    if isinstance(ddsArgs['ddsStartAddr'], str):
        ddsArgs['ddsStartAddr'] = int(ddsArgs['ddsStartAddr'], 16)
    
    with open(phyreFile, 'rb') as myfile:
        f = myfile.read()

    if ddsArgs['encode'] is None:
        (ddsArgs['encode'], ddsArgs['ddsStartAddr']) = findEncoding(f)
        print("Encoding: " + ddsArgs['encode'])
        print("DDS start address: " + hex(ddsArgs['ddsStartAddr']))
    else:
        if ddsArgs['ddsStartAddr'] is not None:
            raise Exception("ddsStartAddr must be specified if encoding type is specified " \
            + "(Try 0xa68 for DXT or 0xa69 for ARGB8)")
        print("User supplied encoding: " + ddsArgs['encode'])
        print("User supplied start address: " + hex(ddsArgs['ddsStartAddr']))
    encode = encode0[ddsArgs['encode']]
            
    (width, height, mips) = getHeaderData(f)
    if (ddsArgs['width'] is None) != (ddsArgs['height'] is None): # biconditional and
        raise Exception('Width and height must be specified together')
    elif ddsArgs['width'] is None:
        (ddsArgs['width'], ddsArgs['height'])= (width, height)
        print("Extracted resolution: %dx%d" % (ddsArgs['width'], ddsArgs['height']))
    else:
        print("User provided resolution: %dx%d" % (ddsArgs['width'], ddsArgs['height']))
        
    if ddsArgs['mipMaps'] is None:
        print("Number of mip maps: %d" % mips)
        ddsArgs['mipMaps'] = mips
    else:
        print("User provided number of mip maps: %d" % ddsArgs['mipMaps'])

    header=buildHeader()
    with open(ddsFile, 'wb') as myfile:
        myfile.write(header + f[ddsArgs['ddsStartAddr']:])
    print("File written to: " + ddsFile)
    
#------------------------------------------------------------------------------
def findEncoding(dds_data):
    # Determine encoding by searching data structure
    
    for key, value in encode0.items():
        s = dds_data.find(str.encode(key))
        if s >= 0:
            startaddr = s + len(key) + 0x26
            return (key, startaddr)
    raise Exception('Encoding scheme could not be found')

#------------------------------------------------------------------------------
def getHeaderData(f):
    # Find resolution and number of mip maps
    import math

    match = f.find(b"PS3Data")
    if match<0:
        raise Exception("Could not find start of header data")
    pos = match+16*3
    mips = struct.unpack_from('I', f, pos)[0]
    pos += 16  
    (width, height) = struct.unpack_from('2I', f, pos)
    if (math.log2(width) % 1) != 0 :
        print("WARN: Width not a power of 2")
    elif max(width,height) > 4096:
        print("WARN: Large width or height")
    elif min(width,height) < 1:
        print("WARN: Small width or height")
    elif math.ceil(math.log2(max(width, height))) < mips:
        print("WARN: More mipmaps than expected")
    return(width, height, mips)
    
#------------------------------------------------------------------------------
def buildHeader():  
    # build DDS header, assume DXT5
    
    def uf(x): return struct.pack('I', x)
    
    # dwFlags flags
    ddsd = {'caps': 0x1, 'height': 0x2, 'width': 0x4, 'pitch': 0x8, \
            'pixelFormat': 0x1000, 'mipMapCount': 0x20000, \
            'linearSize': 0x80000, 'depth': 0x800000
           }
    
    # dwCaps flags
    ddscaps = {'complex': 0x8, 'mipMap': 0x400000, 'texture': 0x1000}
    
    # dwCaps2 flags
#    ddscaps2 = {'cubeMap': 0x200, 'volume': 0x200000, \
#                'positiveX': 0x400,   'negativeX': 0x800, \
#                'positiveY': 0x1000,  'negativeY': 0x2000, \
#                'positiveZ': 0x4000,   'negativeZ': 0x8000                
#               }
        
    dwSize = uf(124)
    dwFlags0 = ddsd['caps'] + ddsd['height'] + ddsd['width'] \
                 + ddsd['pixelFormat'] + ddsd['mipMapCount']
    dwHeight = uf(ddsArgs['height'])
    dwWidth = uf(ddsArgs['width'])
    dwPitchOrLinearSize = uf(0) # gets set depending on encoding below
    dwDepth = uf(0)
    dwMipMapCount = uf(ddsArgs['mipMaps'])
    dwReserved1 = b''.join([uf(0) for i in range(11)])
    ddspf = buildDdsPixelFormat()
    dwCaps = uf(ddscaps['complex'] + ddscaps['mipMap'] + ddscaps['texture'])
    dwCaps2 = uf(0)
    dwCaps3 = uf(0)
    dwCaps4 = uf(0)
    dwReserved2 = uf(0)
    
    if ddsArgs['encode'][0:3] == 'DXT':
        dwPitchOrLinearSize = uf(max(1, int(((ddsArgs['width'] + 3)/4)))*(encode['bbp']*2))
        dwFlags = uf(dwFlags0 + ddsd['linearSize'])
    elif ddsArgs['encode'] == 'ARGB8':
        dwPitchOrLinearSize = uf(int((ddsArgs['width']*encode['bbp']+7)/8))
        dwFlags = uf(dwFlags0 +ddsd['pitch'])
    else:
        raise Exception("Unexpected encoding type: " + ddsArgs['encode'])
    
    return (b'DDS ' + dwSize + dwFlags + dwHeight + dwWidth \
            + dwPitchOrLinearSize + dwDepth + dwMipMapCount + dwReserved1 \
            + ddspf + dwCaps + dwCaps2 + dwCaps3 + dwCaps4 + dwReserved2 )
           
#------------------------------------------------------------------------------       
def buildDdsPixelFormat():
    # Build DDSPixelFormat structure for header (assume DXT5)
    
    def uf(x): return struct.pack('I', x)
    
    # dwFlags flags
    ddpf = {'alphaPixels': 0x1, 'alpha': 0x2, 'fourCC': 0x4, 'rgb': 0x40, \
            'yuv': 0x200, 'luminance': 0x20000 
            }
    
    dwSize = uf(32)

    if ddsArgs['encode'][0:3] == 'DXT':
        dwFlags = uf(ddpf['fourCC'])
        dwFourCC = str.encode(ddsArgs['encode'])
        dwRGBBitCount = uf(0)
        dwRBitMask = uf(0)
        dwGBitMask = uf(0)
        dwBBitMask = uf(0)
        dwABitMask = uf(0)
    elif ddsArgs['encode'] == 'ARGB8':
        dwFlags = uf(ddpf['alphaPixels'] + ddpf['rgb'])
        dwFourCC = uf(0)
        dwRGBBitCount = uf(encode['bbp'])
        dwRBitMask = uf(0x00ff0000)
        dwGBitMask = uf(0x0000ff00)
        dwBBitMask = uf(0x000000ff)
        dwABitMask = uf(0xff000000)
    else:
        raise Exception("Unexpected encoding type: " + ddsArgs['encode'])
    
    return(dwSize + dwFlags + dwFourCC + dwRGBBitCount + dwRBitMask \
           + dwGBitMask + dwBBitMask + dwABitMask)