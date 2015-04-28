from __future__ import division
from skimage.feature import hog
from skimage import exposure
from sklearn import svm, cross_validation
import AUVSIcv
import numpy as np
import cv2
import glob
import os
import time
import pickle

VISUALIZE = False

def learn():
    base_path = os.environ['AUVSI_CV_DATA']
    samples = np.load(os.path.join(base_path, 'patch_samples.npy'))
    labels = np.load(os.path.join(base_path, 'patch_labels.npy'))

    print len(labels)
    
    kf = cross_validation.StratifiedKFold(labels, n_folds=4, shuffle=True)
    
    svc = svm.SVC(kernel='linear')
    
    for c in range(3):
        for train_index, test_index in kf:
            svc.fit(samples[c][train_index], labels[train_index])
            
            print c, svc.score(samples[c][test_index], labels[test_index])
            

def learn_save():
    base_path = os.environ['AUVSI_CV_DATA']
    samples = np.load(os.path.join(base_path, 'patch_samples.npy'))
    labels = np.load(os.path.join(base_path, 'patch_labels.npy'))

    print 'learning classifier'
    svc = svm.SVC(kernel='linear')
    svc.fit(samples[0], labels)
    
    print 'saving classifier'
    with open(os.path.join(base_path, 'linear_svc.pkl'), 'wb') as f:
        s = pickle.dump(svc, f)
        

def test_classifier():
    base_path = os.environ['AUVSI_CV_DATA']
    imgs_paths = sorted(glob.glob(os.path.join(base_path, 'test', '*.jpg')))
    data_paths = [os.path.splitext(path)[0]+'.json' for path in imgs_paths]
    
    with open(os.path.join(base_path, 'linear_svc.pkl'), 'rb') as f:
        clf = pickle.load(f)
    
    #
    # Load image and image data
    #
    for img_path, data_path in zip(imgs_paths, data_paths):
        print 'Extracting patches from image', img_path
        
        img = AUVSIcv.Image(img_path, data_path)
        
        patches = img.createPatches(patch_size=(100, 100), patch_shift=20)
            
        for patch in patches:
            patch_gray = cv2.cvtColor(patch, cv2.cv.CV_RGB2HSV)[..., 0]
            fd = hog(patch_gray, orientations=8, pixels_per_cell=(16, 16),
                            cells_per_block=(1, 1), visualise=False)
            
            if clf.predict(fd)[0] == 1:
                cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
                cv2.imshow('image', patch)
                cv2.waitKey(0)

    cv2.destroyAllWindows()

def extract():

    base_path = os.environ['AUVSI_CV_DATA']
    imgs_paths = sorted(glob.glob(os.path.join(base_path, '*.jpg')))
    data_paths = [os.path.splitext(path)[0]+'.json' for path in imgs_paths]
    
    #
    # Load image and image data
    #
    with_target_flag = 0
    samples = [[], [], []]
    labels = []
    
    for img_path, data_path in zip(imgs_paths, data_paths):
        print 'Extracting patches from image', img_path
        
        img = AUVSIcv.Image(img_path, data_path)
        
        patches = img.createPatches(patch_size=(100, 100), patch_shift=20)
            
        for patch in patches:
            target = AUVSIcv.randomTarget(
                altitude=0,
                longitude=img.longitude,
                latitude=img.latitude
            )
            
            if with_target_flag:            
                img.pastePatch(patch=patch, target=target)

            for c in range(3):
                patch_gray = cv2.cvtColor(patch, cv2.cv.CV_RGB2HSV)[..., c]
                fd = hog(patch_gray, orientations=8, pixels_per_cell=(16, 16),
                                cells_per_block=(1, 1), visualise=False)
                samples[c].append(fd)
            
                if VISUALIZE:
                    hog_image_rescaled = exposure.rescale_intensity(hog_image, in_range=(0, 0.02))
                    
                    cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
                    cv2.imshow('image', hog_image_rescaled)
                    cv2.waitKey(0)
    
            labels.append(with_target_flag)
            
            with_target_flag = 1 - with_target_flag
            
    samples = np.array(samples)
    labels = np.array(labels)
    
    if VISUALIZE:
        cv2.destroyAllWindows()

    np.save(os.path.join(base_path, 'patch_samples.npy'), samples)
    np.save(os.path.join(base_path, 'patch_labels.npy'), labels)


if __name__ == '__main__':
    #extract()
    #learn_save()
    test_classifier()