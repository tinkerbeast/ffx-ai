# -*- coding: utf-8 -*-

import phyre, importlib, os
importlib.reload(phyre)

# 1 or 2
ffx=1

# pc, npc, mon, obj, skl, sum, or wep
tp = 'pc'

# model number (no leading zeros)
num = 106

ffxBaseDir=r'C:\SteamLibrary\steamapps\common\FINAL FANTASY FFX&FFX-2 HD Remaster\data\FFX_Data_VBF\ffx_data\gamedata\ps3data\chr'
ffx2BaseDir=r'C:\SteamLibrary\steamapps\common\FINAL FANTASY FFX&FFX-2 HD Remaster\data\FFX2_Data_VBF\ffx-2_data\gamedata\ps3data\chr'
baseDir=[ffxBaseDir, ffx2BaseDir]



types={'pc':'c', 'npc':'n', 'mon':'m', 'obj':'f', 'skl':'k', 'sum':'s', 'wep':'w'}

file=baseDir[ffx-1]
cs = types[tp] + '%03d' % num
meshFile = os.path.join(file, tp, cs,'mdl','d3d11', cs + r'.dae.phyre')
ddsFile = os.path.join(file, tp, cs, 'tex', 'd3d11', cs + r'.dds.phyre')

outFile = r'mytest.obj'
outFile2 = r'mytest.dds'
#outFile = None
phyre.extractMesh(meshFile,outFile, debug=False)
print("\n")
if os.path.isfile(ddsFile):
    phyre.extractDDS(ddsFile, outFile2)
else: 
    print("DDS file not found. Skipping")