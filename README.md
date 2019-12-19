About
=====

This is an overly ambitious project where I intend to develop an AI to completely play Final Fantasy X.

The story
=========

When I first played ffx, I thought how boring the fight system was. You couldn't button mash to beat the enemies, but writing an AI would be so easy.

So, so many years later (with image recognition a well developed field now),  I am writing an AI.


The first steps
---------------

The first steps is obviously to get the character and monster models to train the nerual network. However, this is actually lot harder since, I don't have any experience in game moding. So, building on the shoulders of everyone else - The https://forum.xentax.com/ forums. Honestly these guys have a tons of resource on game modding (including very advanced papers on shading etc).


Note: Later I found this link http://forums.qhimm.com/index.php?topic=17946.0, which would have sped up things.


### First first step

The FFX data is stored in "FFX_Data.vbf" file. The vbf format is nothing but a custom archive format. A quick search will land you at https://forum.xentax.com/viewtopic.php?f=10&t=14340 . Which in turn will take you to https://github.com/topher-au/VBFTool.

As a C# noob, I toyed around for a few hours before I could compile the tool. The tool worked seamelessyly and extracted the vbf file into the following dir structure:

```
.
├── ffx_data
│   └── gamedata
│       └── ps3data
│           ├── battle
│           ├── btlmap
│           ├── chr
│           ├── event
│           ├── flash
│           ├── fonts
│           ├── help
.......................
│           ├── texturevideo
│           ├── video
│           └── yonishi_data
├── ffx_ps2
........................
├── metamenu
.......................
└── version_config
.......................
```

After some searching I realised the monster models are store in 

ffx_data/gamedata/ps3data/chr/mon

But how to render them?

### Converting the models to a common format

The folder structure is:

```
m001/
├── m001.ah
├── m001.ahwin32
├── mdl
│   └── d3d11
│       └── m001.dae.phyre
└── tex
    └── d3d11
        └── m001.dds.phyre
```

While .dae is a standard collada format. And .dds is a standard texture format. Neither of them were openable in blender or gimp - Why? The .phyre format coverts these open formats to some non-standard format. Info on phyre engine https://en.wikipedia.org/wiki/PhyreEngine, https://zenhax.com/viewtopic.php?t=7573.

So, https://forum.xentax.com/viewtopic.php?p=126978#p126978 guys to the rescue again. They made a nice little tool ffx_mesh_extractor.zip which solves our problem.

I wrote the code below for my own convenience.


```
import phyre, importlib, os
importlib.reload(phyre)

meshFile = '/path_to_model/m001.dae.phyre'
ddsFile = '/path_to_model/m001.dds.phyre'

if __name__ == '__main__':
    outFile = r'mytest.obj'
    outFile2 = r'mytest.dds'
    #outFile = None
    phyre.extractMesh(meshFile,outFile, debug=False)
    print("\n")
    if os.path.isfile(ddsFile):
        phyre.extractDDS(ddsFile, outFile2)
    else:
        print("DDS file not found. Skipping")
```

### Rendering the image

This took me almost 3 days just to render one thing in blender. I posted this https://forum.xentax.com/viewtopic.php?f=16&t=21502 question on xentax forum, but no one helped.

So I decided to learn blender. Firstly, moving to latest (2.8) blender made a lot of difference. Secondly following the https://www.youtube.com/watch?v=TPrnSACiTJ4 tutorial series to some depth also made a lot of difference (getting familiar with blender basic of basic concepts obviously helps). However the video that did the trick for me was https://www.youtube.com/watch?v=fZSD7pVIUkY (not that I would be able to follow it without the previous series).

In case that video get deleted or something, I am writing down the steps. Exact blender version I am using is Blender 2.81 (sub 16).

* Import model (obj file)
* Select model
* Set render mode to "material preview" (hotkey z)
* In model properties go to texture properties
* Chane "Base color option" to "Image texture"
* "Open", then load dds file
* That it !!! magic

### Rendering programatically

Good starting tutorial https://www.youtube.com/watch?v=rHzf3Dku_cE.

Good reference script https://blender.stackexchange.com/questions/39303/blender-script-import-model-and-render-it

However, I still got stuck (but only for a day now, since I finally understood a little blender). I posted a question on https://blender.stackexchange.com/questions/161219/apply-texture-to-a-model-via-blender-script this time. However, I was able to solve it myself:

Add again two days later my little project got complex enough to put it up on github.