# -*- coding: utf-8 -*-

import os
import shutil
from phyre import extractMesh, extractDDS
import sys

ffxBaseDir=r'C:\SteamLibrary\steamapps\common\FINAL FANTASY FFX&FFX-2 HD Remaster\data\FFX_Data_VBF\ffx_data\gamedata\ps3data\chr'
ffx2BaseDir=r'C:\SteamLibrary\steamapps\common\FINAL FANTASY FFX&FFX-2 HD Remaster\data\FFX2_Data_VBF\ffx-2_data\gamedata\ps3data\chr'
baseDir=[ffxBaseDir, ffx2BaseDir]

types={'pc':'c', 'npc':'n', 'mon':'m', 'obj':'f', 'skl':'k', 'sum':'s', 'wep':'w'}
ffx0=[1,2]
tps=['pc','npc','mon','obj','skl','sum','wep']


for ffx in ffx0:
    for tp in tps:
        
        if ffx==1: 
            gamestr = "FFX"
        else:
            gamestr = "FFX2"
        
        logFile = gamestr + "_" + tp + r"_log.txt"
            
        f=open(logFile, 'w')
        stdout0 = sys.stdout
        sys.stdout = f
        for i in range(1000):
            cs = types[tp] + '%03d' % i
            thisDir = os.path.join(baseDir[ffx-1], tp, cs)
            if not os.path.exists(thisDir):
                continue
            print("\n\n\n\n")
            print("=====================================================================")
            print("Found " + thisDir)
            daeFile=os.path.join(thisDir,'mdl','d3d11',cs+r'.dae.phyre')
            ddsFile=os.path.join(thisDir,'tex','d3d11',cs+r'.dds.phyre')
            dumpDir = os.path.join(gamestr, tp, cs)
            if os.path.exists(dumpDir):
                shutil.rmtree(dumpDir)
            os.makedirs(dumpDir)
            objFile=os.path.join(dumpDir, cs+r'.obj')
            ddsFile2=os.path.join(dumpDir, cs+r'.dds')
            
            try:
                extractMesh(daeFile, objFile)
            except Exception as e:
                print ("Failed:" + repr(e))
            
            if os.path.exists(ddsFile):
                print("\n\n\n")
                try:
                    extractDDS(ddsFile, ddsFile2)
                except Exception as e:
                    print("Failed: " + repr(e))
            else:
                print("\n\n\nDDS file not found. Skipping")
                
        f.close()
        sys.stdout = stdout0
        print("Done with %s %s" % (gamestr, tp))