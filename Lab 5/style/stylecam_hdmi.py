#!/usr/bin/env python3
import argparse
import time
from pathlib import Path
import cv2
import numpy as np
from tflite_runtime.interpreter import Interpreter

FIX_W = 380
FIX_H = 285
DISPLAY_W = 640
DISPLAY_H = 480

def load_interpreter(path, threads=4):
    it = Interpreter(model_path=path, num_threads=threads)
    it.allocate_tensors()
    return it

def smart_set_tensor(it, idx, arr_float01):
    det = next(d for d in it.get_input_details() if d['index']==idx)
    dtype = det['dtype']
    if np.issubdtype(dtype, np.floating):
        it.set_tensor(idx, arr_float01.astype(np.float32))
        return
    qp = det.get('quantization_parameters',{})
    scales = qp.get('scales',None)
    zps    = qp.get('zero_points',None)
    if not scales:
        scale=det.get('quantization',(1.0,0))[0]
        zero =det.get('quantization',(1.0,0))[1]
    else:
        scale=float(scales[0])
        zero=int(zps[0]) if zps is not None else 0
    q=np.round(arr_float01/scale + zero)
    q=np.clip(q,np.iinfo(dtype).min,np.iinfo(dtype).max).astype(dtype)
    it.set_tensor(idx,q)

def postprocess_rgb(it,out_idx):
    out = it.get_tensor(out_idx)
    det = next(d for d in it.get_output_details() if d['index']==out_idx)
    dt = det['dtype']
    if np.issubdtype(dt,np.floating):
        rgb = np.clip(out[0]*255.0,0,255).astype(np.uint8)
    else:
        qp=det.get('quantization_parameters',{})
        scale=qp['scales'][0]; zp=qp['zero_points'][0]
        rgb=np.clip((out[0]-zp)*scale*255.0,0,255).astype(np.uint8)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

def run_style_predict(p, style_img):
    ii=p.get_input_details()[0]['index']
    oo=p.get_output_details()[0]['index']
    smart_set_tensor(p,ii,style_img)
    p.invoke()
    return p.get_tensor(oo)

def identify_transform_inputs(tr):
    ids = tr.get_input_details()
    idc=None
    for d in ids:
        shp=d['shape']
        if len(shp)==4 and shp[-1]==3:
            idc=d['index']; break
    ids_other=[d['index'] for d in ids if d['index']!=idc]
    return idc, ids_other[0]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--predict",default="style_predict_fast.tflite")
    ap.add_argument("--transform",default="style_transform_fast.tflite")
    ap.add_argument("--styles_dir",default="styles")
    ap.add_argument("--cam",type=int,default=0)
    ap.add_argument("--threads",type=int,default=4)
    ap.add_argument("--alpha",type=float,default=1.0)
    ap.add_argument("--mirror",dest="mirror",action="store_true",default=True)
    ap.add_argument("--no-mirror",dest="mirror",action="store_false")
    ap.add_argument("--skip",type=int,default=0)
    args=ap.parse_args()

    styles = sorted(list(Path(args.styles_dir).glob("*.jpg"))+
                    list(Path(args.styles_dir).glob("*.png")))
    if not styles: raise RuntimeError("No styles found")
    idx=0

    pred = load_interpreter(args.predict,args.threads)
    trf  = load_interpreter(args.transform,args.threads)

    cap=cv2.VideoCapture(args.cam)
    if not cap.isOpened(): raise RuntimeError("No camera")

    win="StyleCam"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, DISPLAY_W, DISPLAY_H)

    idc,id_style = identify_transform_inputs(trf)
    trf.resize_tensor_input(idc,(1,FIX_H,FIX_W,3),strict=False)
    trf.allocate_tensors()
    out_idx=trf.get_output_details()[0]['index']

    def load_style(path):
        img=cv2.imread(str(path))
        rgb=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        rgb=cv2.resize(rgb,(256,256))/255.0
        sb=run_style_predict(pred,rgb[None,...])
        if sb.ndim==2: sb=sb.reshape((1,1,1,100))
        return sb.astype(np.float32)

    sb = load_style(styles[idx])
    print("Controls: [ ] style | a/z alpha | m mirror | k/j skip | q quit")

    frame_id=0
    while True:
        ok,frame=cap.read()
        if not ok: continue
        if args.mirror: frame=cv2.flip(frame,1)
        small=cv2.resize(frame,(FIX_W,FIX_H))
        rgb=small[:,:,::-1]/255.0
        rgb=rgb[None,...]
        if frame_id%(args.skip+1)==0:
            smart_set_tensor(trf,idc,rgb)
            smart_set_tensor(trf,id_style,sb)
            trf.invoke()
            out=postprocess_rgb(trf,out_idx)
        else:
            out=small.copy()
        if args.alpha<1:
            out=cv2.addWeighted(out,args.alpha,small,1-args.alpha,0)
        disp=cv2.resize(out,(DISPLAY_W,DISPLAY_H),interpolation=cv2.INTER_NEAREST)
        cv2.imshow(win,disp)
        k=cv2.waitKey(1)&0xFF
        if k==ord('q'): break
        elif k==ord('['): idx=(idx-1)%len(styles); sb=load_style(styles[idx])
        elif k==ord(']'): idx=(idx+1)%len(styles); sb=load_style(styles[idx])
        elif k==ord('m'): args.mirror=not args.mirror
        elif k==ord('a'): args.alpha=min(1,args.alpha+0.05)
        elif k==ord('z'): args.alpha=max(0,args.alpha-0.05)
        elif k==ord('k'): args.skip=min(4,args.skip+1)
        elif k==ord('j'): args.skip=max(0,args.skip-1)
        frame_id+=1

    cap.release()
    cv2.destroyAllWindows()

if __name__=="__main__":
    main()
