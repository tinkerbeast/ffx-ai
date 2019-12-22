# -*- coding: utf-8 -*-

import logging
import os
import pandas as pd
import shutil
import subprocess
import tempfile
from multiprocessing.pool import ThreadPool

import bg_convert

from thirdparty_xentax import phyre

def model_gather(chr_path, filter_dirs=[]):
    model_data = []
    sub_dirs = os.listdir(chr_path) if len(filter_dirs) == 0 else filter_dirs
    for sub_dir in sub_dirs:
        sub_dir_path = os.path.join(chr_path, sub_dir)
        models = os.listdir(sub_dir_path)
        for model in models:
            mesh_file = os.path.join(sub_dir_path, model, 'mdl', 'd3d11', model + '.dae.phyre')
            texture_file = os.path.join(sub_dir_path, model, 'tex', 'd3d11', model + '.dds.phyre')
            if os.path.exists(mesh_file) and os.path.exists(texture_file):
                model_data.append({'name': sub_dir + '_' + model, 'mesh': mesh_file,'texture': texture_file})
            else:
                logging.warning('Files not present: ' + mesh_file + ' or ' + texture_file)
    return model_data

def model_extract(model_data):
    tmp_dir = tempfile.mkdtemp()
    logging.info('Extracting models into directory, dir=' + tmp_dir)
    for model in model_data:
        out_mesh = os.path.join(tmp_dir, model['name'] + '.obj')
        out_texture = os.path.join(tmp_dir, model['name'] + '.dds')
        phyre.extractMesh(model['mesh'], out_mesh, debug=False)
        phyre.extractDDS(model['texture'], out_texture, debug=False)
    return tmp_dir


def render_job(model_name, obj_path, texture_path, bg_path, dist_path, angle):
    print('{} {} {}'.format(angle, bg_path, model_name))
    instr ='\n'.join([model_name, obj_path, texture_path, bg_path, dist_path, angle]).encode()    
    out = subprocess.check_output("blender --background --python blender_render.py", stderr=subprocess.STDOUT, input=instr, shell=True)
    logging.info('Blender out=' + str(out))
    #print(out.decode('utf-8'))


def make_bgs(bg_path, tmp_dir):    
    files = os.listdir(bg_path)    
    outs = []
    for file in files:
        src_file = os.path.join(bg_path, file)
        outs.append(bg_convert.bg_convert(src_file, tmp_dir))
    return outs

def make_model_map(map_file):
    model_map = {}
    with open(map_file) as fd:
        lines = fd.readlines()
    #
    for line in lines:
        if line.startswith('# '):
            classname = line.split(' ')[1].rstrip('\n')
        elif line.startswith('#'):
            pass
        else:
            tokens = line.split('\t')
            model_name = 'mon_m{:03d}'.format(int(tokens[0]))
            model_map[model_name] = classname
            #model_map['web'].append(tokens[1])            
    return model_map
            

def get_triplet(angles, bgs, models):
    for a in angles:
        for b in bgs:
            for m in models:
                yield (a, b, m)


if __name__ == '__main__':
    # get available models
    chr_path = '/media/rishin/20ACFF83ACFF5230/Users/rishin/Desktop/ffxx/ffx_data/gamedata/ps3data/chr'
    bg_path = '/home/rishin/workspace/ffx-ai/assets/'
    dist_path = '/home/rishin/workspace/ffx-ai/dist'
    map_path = '/home/rishin/workspace/ffx-ai/enemy_map.txt'
    # 
    angles_front = [15, 30, 45, 60, 75, 345, 330, 315, 300, 285] # [15, 30, 45, 60, 75, -15, -30, -45, -60, -75]
    angles_back = [105, 120, 135, 150, 165, 255, 240, 225, 210, 195] # [105, 120, 135, 150, 165, -105, -120, -135, -150, -165]
    all_angles = angles_front + angles_back
    #
    model_map = make_model_map(map_path)
    model_filter = model_map.keys()
    #print(model_filter)
    #
    model_data = model_gather(chr_path, ['mon'])
    model_data_filtered = [m for m in model_data if m['name'] in model_filter]
    tmp_dir = model_extract(model_data_filtered)
    #print(model_data)
    print(tmp_dir)
    #
    bg_tmp_dir = tempfile.mkdtemp()
    bg_data = make_bgs(bg_path, bg_tmp_dir)
    #print(bg_data)
    print(bg_tmp_dir)
    # parrallelise jobs
    tp = ThreadPool(12)
    # render models
    xy_map = {'id': [], 'cls': []}
    xxx = 0
    for angle, bg, model in get_triplet(all_angles, bg_data, model_data_filtered):
        model_name = model['name']
        obj_path = os.path.join(tmp_dir, model_name + '.obj')
        texture_path = os.path.join(tmp_dir, model_name + '.dds')
        bg_alt_path = os.path.join(bg_tmp_dir, bg)
        out_path = os.path.join(dist_path, '{}_{}_{}.png'.format(model_name, bg, angle))
        class_suffix = '_front' if angle in angles_front else '_back'
        #
        xy_map['id'].append(out_path)
        xy_map['cls'].append(model_map[model_name] + class_suffix)
        # run subprocess        
        tp.apply_async(render_job, (model_name, obj_path, texture_path, bg_alt_path, out_path, str(angle)))
    
    tp.close()
    tp.join()
    #
    df = pd.DataFrame(xy_map)
    df.to_csv(dist_path + '/img_map.csv')
    # cleanup
    shutil.rmtree(tmp_dir)
    shutil.rmtree(bg_tmp_dir)
