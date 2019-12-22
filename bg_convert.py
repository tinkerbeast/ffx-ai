import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
import uuid 

def _padd_image(aspect_ratio, img, color=(128, 128, 128)):
    im_w = img.shape[1]
    im_h = img.shape[0]
    im_h_target = (im_w / aspect_ratio[0]) * aspect_ratio[1]
    im_w_target = (im_h / aspect_ratio[1]) * aspect_ratio[0]
    if im_h < im_h_target:
        padding = int((im_h_target - im_h) / 2)
        res = cv2.copyMakeBorder(img, padding, padding, 0, 0, cv2.BORDER_CONSTANT, value=color)
        return res
    elif im_w < im_w_target:
        padding = int((im_w_target - im_w) / 2)
        res = cv2.copyMakeBorder(img, 0, 0, padding, padding, cv2.BORDER_CONSTANT, value=color)
        return res
    else:
        return ValueError('Illegal state', aspect_ratio, img.shape)

def _crop_image(aspect_ratio, img):
    im_w = img.shape[1]
    im_h = img.shape[0]
    im_h_target = (im_w / aspect_ratio[0]) * aspect_ratio[1]
    im_w_target = (im_h / aspect_ratio[1]) * aspect_ratio[0]
    if im_h > im_h_target:
        padding = int((im_h - im_h_target) / 2)
        return img[padding:(im_h-padding), :, :]
    elif im_w > im_w_target:
        padding = int((im_w - im_w_target) / 2)
        return img[:, padding:(im_w-padding), :]
    else:
        return ValueError('Illegal state', aspect_ratio, img.shape)

def _cv2_resize(img, dsize, mode='none', interpolation=cv2.INTER_AREA, color=(128, 128, 128)):
    preimage = None
    if mode == 'none':
        preimage = img
    elif mode == 'padd':
        preimage = _padd_image(dsize, img, color=color)
    elif mode == 'crop':
        preimage = _crop_image(dsize, img)
    #
    return cv2.resize(preimage, dsize, interpolation=interpolation)

def _segmentimage(img, wratio, hratio):
    im_w = img.shape[1]
    im_h = img.shape[0]
    #
    wmid = int(im_w * wratio)
    hmid = int(im_h * hratio)
    top_left =  img[:hmid, :wmid, :]
    top_right = img[:hmid, wmid:, :]
    bot_left =  img[hmid:, :wmid, :]
    bot_right = img[hmid:, wmid:, :]
    return (top_left, top_right, bot_left, bot_right)


def bg_convert(src_file, dst_dir, width=2520, height=1080):
    idx = uuid.uuid1() 
    dst_name = str(idx.hex)
    # bg
    img = cv2.imread(src_file)
    resized = _cv2_resize(img, (width, height), mode='crop')
    out = os.path.join(dst_dir, dst_name + '-bg.png')
    cv2.imwrite(out, resized)
    # floor
    tl, tr, bl, br = _segmentimage(resized, 0.0, 0.8)
    resized = _cv2_resize(br, (width, width), mode='none')
    out = os.path.join(dst_dir, dst_name + '-fl.png')
    cv2.imwrite(out, resized)
    return dst_name
