import bpy
import math
import mathutils
import ntpath
import os
import sys



def remove_obj_and_mesh(context):
    scene = context.scene
    objs = bpy.data.objects
    meshes = bpy.data.meshes
    images = bpy.data.images
    for img in images:
        images.remove(img)
    for obj in objs:
        #if obj.type == 'MESH':
        #    scene.objects.unlink(obj)
        #    objs.remove(obj)
        pass
    for mesh in meshes:
        meshes.remove(mesh)

        
def load_model(obj_path, dds_path, default_shader='Principled BSDF'):
    # load model
    oldx = set(bpy.data.objects)
    bpy.ops.import_scene.obj(filepath=obj_path)
    newx = set(bpy.data.objects)
    myobj = (newx - oldx).pop()
    # load texture
    oldx = set(bpy.data.images)
    bpy.ops.image.open(filepath=dds_path)
    newx = set(bpy.data.images)
    mytex = (newx - oldx).pop()
    # get material refs
    myobj_material_nodes = myobj.active_material.node_tree.nodes
    myobj_material_links = myobj.active_material.node_tree.links
    # add texture
    node_texture = myobj_material_nodes.new(type='ShaderNodeTexImage')
    node_texture.image = mytex
    # link texture
    my_obj_shader = myobj_material_nodes.get(default_shader)
    myobj_material_links.new(my_obj_shader.inputs["Base Color"], node_texture.outputs["Color"])
    return myobj


def add_bg_image(filename, dist=200, zdist=50, scale=200):    
    basename = ntpath.basename(filename)
    dirname = ntpath.dirname(filename)
    # postion and rotations of planes
    rots = [ [90,  180, 0],
             [90,  180, 90],             
             [90,  180, 180],
             [90,  180, 270]]
    locs = [ [0,  -dist, -zdist],
             [-dist,  0, -zdist],             
             [0,  dist,  -zdist],
             [dist,  0,  -zdist]]
    # load palnes
    for i in range(4):
        bpy.ops.import_image.to_plane(files=[{"name":basename}], directory=dirname, relative=False)
        plane_obj = bpy.context.active_object
        plane_obj.scale = (scale, scale, 1)
        plane_obj.rotation_euler = [math.radians(a) for a in rots[i]]
        plane_obj.location = locs[i]

    
def add_floor_image(filename, zdist, scale=200):
    basename = ntpath.basename(filename)
    dirname = ntpath.dirname(filename)
    bpy.ops.import_image.to_plane(files=[{"name":basename}], directory=dirname, relative=False)
    plane_obj = bpy.context.active_object
    plane_obj.scale = (scale, scale, 1)    
    rot_transform = [math.radians(a) for a in (180.0, 180.0, -180.0)]
    plane_obj.rotation_euler = rot_transform
    plane_obj.location = (0, 0, zdist)


def setup_scene(obj, scene, cam_radius, front_angle=0, light_radius=150, clip_end=500):
    # TODO: setup cam location based on obj size
    # setup values
    cam_angle = [math.radians(a) for a in (-90, 0, -front_angle)]
    front_angle = math.radians(front_angle)
    cam_location = (cam_radius*math.sin(front_angle), cam_radius*math.cos(front_angle), 0)
    lamp_location = (light_radius*math.sin(front_angle), light_radius*math.cos(front_angle), 0)
    # setup camera
    camera = scene.objects.get('Camera')
    camera.location = cam_location    
    camera.rotation_euler = cam_angle
    camera.data.clip_end = clip_end
    # setup lamp
    lamp = camera = scene.objects.get('Light')
    lamp.location = lamp_location
    lamp.rotation_euler = cam_angle
    lamp.data.type = 'AREA'
    lamp.data.energy = 400000


def render_scene(scene, filename, res_x=300, res_y=300, format='PNG'):
    scene.render.image_settings.file_format=format
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.filepath = filename
    bpy.ops.render.render(write_still=True)


def run(idx):
    print('INFO: Getting parameters')
    #out_name = '%03d' % idx
    #obj_path = '/tmp/tmp1x3_g5r3/mon_m{}.obj'.format(out_name)
    #tex_path = '/tmp/tmp1x3_g5r3/mon_m{}.dds'.format(out_name)
    out_name = sys.stdin.readline().rstrip('\n')
    obj_path = sys.stdin.readline().rstrip('\n')
    tex_path = sys.stdin.readline().rstrip('\n')
    img_path = sys.stdin.readline().rstrip('\n')
    out_path = sys.stdin.readline().rstrip('\n')
    angle = int(sys.stdin.readline().rstrip('\n'))


    print('INFO: Loading models')
    remove_obj_and_mesh(bpy.context)
    xobj = load_model(obj_path, tex_path)    
    gen_scale = max(xobj.dimensions) / 14.5

    print('INFO: Loading backgrounds')
    add_bg_image(img_path + '-bg.png')
    add_floor_image(img_path + '-fl.png', 10+xobj.dimensions[2]/2)

    print('INFO: Rendering scenes')
    #fa = [0, 45, 90, 135, 180, -135, -90, -45]
    fa = [angle]
    for i in range(len(fa)):
        setup_scene(xobj, bpy.data.scenes[0], 30.0 + 10*gen_scale, front_angle=fa[i])
        render_scene(bpy.data.scenes[0], out_path)
    print('INFO: Rendering scenes')


run(0)