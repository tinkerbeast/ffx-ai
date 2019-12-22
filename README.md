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

However, I still got stuck (but only for a day now, since I finally understood a little blender). I posted a question on https://blender.stackexchange.com/questions/161219/apply-texture-to-a-model-via-blender-script this time. However, I was able to solve it myself - See the `load_model` function in `blender_renderer.py`.

Now there was no stopping me, and with small hiccups, we progressed pretty well. Since this baby got more and more complex, I put it up on github.

Sidenote: Please don't judge me at the horrible way the blender script is written (I'm a 3d graphics noob) - Help me if you can.

### A quick digression 

At this point I was able to generate 2624 images (about 375 MiB), and upon manual inspection they mostly looked ok. A point to mention here is that I was very glad I multithreaded the render code (badly done, but still ...) . The execution took about 19 execution minutes whereas real execution was only 2 and half minutes.

At this point I went and did a lot of things:

1. I tried collecting background images which would help generate more cases. I tried to do this in a reproducible manner by getting permalinks of free images and downloading them via script. However I realised that even free image sites don't give permalinks (Booooo!!!). So after wasting a solid two hours I moved on.

2. I also realised that in order to get all the image dimensions, perspective, etc right, I had to revisit the game. So I did and took multiple screenshots of the different maps, enemies etc.

3. I got a bit greedy at this point and already started modelling the images I collected - And whoaa 62% accuracy on the training set. This excitement was shortlived as the test accuracy was 0%. The test was bad since there was one completely black monster and it just detected the black areas in the background. The training accuracy could be improved a lot also:
    * Visually I could not tell the monster from certain pictures. So how can the ML work if human accuracy is low. This mainly happened because front or side perspectives on certain monsters didn't show anythin (the monster was flat).
    * Several monsters I went throught looked exactly like one another (not just shape, colour also).
    * The front and rear perspectives looked very different for the same monster.

So I had a lot of work ahead of me:

* Manually collect background image (will make it script later)
* Manually figure out game box sizes for monsters, cursors, characters etc. Also analyse variances in these.
* Automatically generate valid perspective of monsters.
* Manually map monster classes.
* Automatically double monster classes by seggregating into front and behind.
* Optionally - When mapping monster classes link them to a site which can be scraped for information.

* Automatically add a background class.
* Tightly cropped image

A lot of manual work ahead :( T_T.


### A change in work direction

So I have been manually categorising enemy models. While so I learned that some of the models where in a very differnet shape than the way they appear in games. For example, the elements where broken down into pieces and not arranged. The wings on the sinscale was stuck together. The moustache on the coeurl or whatever it's name was pointed very long horizontally. And the horns on the ruminant type species were pointed. This made me despair - 3d model manipulation wasn't something I had intended on doing for this project. So I have decided to change the way I was working.

Project managers would love the term I am going to use next - I am going lean, mean, agile. Instead of building that pefect monster model, I will focus on a minimu viable model and progess from there. The reason? Well after so many years in software engineering I have realised this project is going to be fairly unpredicatble. Rather than getting each phase perfect, making the whole thing together in a bad way and improving upon that would make sense. So my definition of done for the next two weeks?

1. Map the following species of monsters to corrsponding graphic-models {helms imps lupine flan reptile bird wasp evil-eye plant sahagin drake sinscale bomb fungus ruminant}. Full mapping need not be done since models may have extras and some special species models are there. [DONE]
2. Manually collect background images for rendering
3. Based on 1 and 2, build a high accuracy (> 75%) ML-model.
4. [Optional] Use the model for R-CNN predictions
6. [Optional] Start work on YOLO with these data

Note: The species mentioned in point 1 probably covers 80% of final fantasy battles (if not more). Elements would be the only problem. Also, the battles are dependent on the species type rather than the exact type (except for magic based enemies - but we will cross that bridge later).


20160 images later
------------------

So I manually collected background images, and with the reduced set of classes I generated these images. I have to note down two dumb things I did:

* I started passing the angle paramter to the blender script (this slowed down things tremendously since I am restarting a blender process every time I generate a single image).
* I don't know why I thought I need to differentiate between front and rear view - The fully connected layer should absolutely take care of this.


### A little bit of modelling

Coming into step 3 of my DOD - This is necessary to get a sense if the amount of data is enough, what kind of hyperparamters I need to set, etc. To make a long story short, I initally tried with MobileNetv2, but that one seemed to overfit very early - Shouldn't really happen, but maybe a local optima? Though this was a high variance case, I didn't really have more data to add. So I went with local optima theory (even though it's fairly improbable) and tried a InceptionV3. This one gave decent results with 83% accuracy on the validation set. This also overfit the data after 4 epochs, but in between results were still acceptable. So I'll be moving on to YOLO. So, lots of model manipulation, bounding boxes etc again to do. But before that I have decided to add an extra task for this sprint (since step 1,2,3 happened fairly fast):

* I will add the lead character models also.
