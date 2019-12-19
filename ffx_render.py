# -*- coding: utf-8 -*-

import logging
import os
import shutil
import subprocess
import tempfile
from multiprocessing.pool import ThreadPool

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


def render_job(model_name, obj_path, texture_path):    
    instr ='\n'.join([model_name, obj_path, texture_path]).encode()
    out = subprocess.check_output("blender --background --python blender_render.py", stderr=subprocess.STDOUT, input=instr, shell=True)
    logging.info('Blender out=' + str(out))

if __name__ == '__main__':
    # get available models
    chr_path = '/media/rishin/20ACFF83ACFF5230/Users/rishin/Desktop/ffxx/ffx_data/gamedata/ps3data/chr'
    model_data = model_gather(chr_path, ['mon'])
    # extract models in a tmp dir
    tmp_dir = model_extract(model_data)
    # render models
    tp = ThreadPool(6)
    for model in model_data:
        obj_path = os.path.join(tmp_dir, model['name'] + '.obj')
        texture_path = os.path.join(tmp_dir, model['name'] + '.dds')
        # run subprocess
        tp.apply_async(render_job, (model['name'], obj_path, texture_path))
    tp.close()
    tp.join()
    # cleanup
    shutil.rmtree(tmp_dir)