#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
#from matplotlib import pyplot as plt
import numpy as np
#import argparse
import imutils
import cv2
import sys
import time
import spidev
from statistics import mean


def IR_Create():
    spi = spidev.SpiDev() # create spi object
    spi.open(0,0) # open spi port 0, device (CS) 1
    spi.max_speed_hz = 1350000
    return spi

def readChannel(spi, channel):
    val = spi.xfer2([1, (8+channel)<<4, 0])
    data = ((val[1]&3) << 8) + val[2]
    return data

def count_dist(spi):
    v = (readChannel(spi, 0)/1023.0) * 3.3
    dist = 16.2537 * v**4 - 129.893 * v**3 + 382.268 * v**2 - 512.611 * v + 301.439
    return dist

def measure_average(spi):
    dist_list = []
    for i in range(70):
      distance = count_dist(spi)
      time.sleep(0.01)
      dist_list.append(distance)
    dist_list.sort()
    dist_list = dist_list[10:60]
    result = mean(dist_list)
    return result

def IR_measure_distance():
    spi = IR_Create()
    distance = measure_average(spi)
    spi.close()
    return distance

########################################################

# 計算圖片中點
def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)

# 啟動一個鏡頭拍照
def camrea_img_1():
    #choose camera
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    cap.set(1, 10.0)

    #fourcc = cv2.VideoWriter_fourcc(*'XVID')
#        while True:
    for i in range(10):
        ret,frame = cap.read()
         # if ret == True:
#        cv2.imshow("frame", frame)
    cv2.imwrite("image.jpg", frame)
#          if cv2.waitKey(1) & 0xFF == ord('q'):
#           print(cap.get(cv2.CAP_PROP_FRAME_COUNT))

#            cv2.imwrite("result.jpg", frame)
#            break

    cap.release()
    cv2.destroyAllWindows()

    return frame

    # 讀取圖片
def read_img(img_path):
    image = cv2.imread(img_path)
    return image

def calculate_pixels_per_metric_up(height):
    new_pixels_per_metric = height * (-0.06961435337107373) + 15.61801518
    return new_pixels_per_metric

def calculate_pixels_per_metric_down(height):
        new_pixels_per_metric = height * (-0.1595383546360724) + 21.841026607
        return new_pixels_per_metric


    #影像處理
def image_processing(img):
    # load the image, convert it to grayscale, and blur it slightly
    image = img.copy()
    # print("processing :", time.now())
    img_RGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(img_RGB, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    ret,thresh1 = cv2.threshold(gray, 110, 255, cv2.THRESH_BINARY)
    ret,thresh2 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    ret,thresh3 = cv2.threshold(gray, 127, 255, cv2.THRESH_TRUNC)
    ret,thresh4 = cv2.threshold(gray, 127, 255, cv2.THRESH_TOZERO)

    return img_RGB

    # 分析圖片計算材積
def dms_counting(img, height, dirc):
    thresh = img
    # perform edge detection, then perform a dilation + erosion to
    # close gaps in between object edges

    edged = cv2.Canny(thresh, 50, 100)
    edged = cv2.dilate(edged, None, iterations=1)
    edged = cv2.erode(edged, None, iterations=1)

    # find contours in the edge map
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]

    # 判斷物件數量
    if len(cnts) <= 0 :
    	print("no object")
    else:
        (cnts, _) = contours.sort_contours(cnts)
        pixelsPerMetric = None
        sum_dim = 0
        real_thing = 0
        # loop over the contours individually
        for c in cnts:
            # if the contour is not sufficiently large, ignore it
            if cv2.contourArea(c) < 500:
                continue
            real_thing +=1

            orig = img.copy()
            box = cv2.minAreaRect(c)
            box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
            box = np.array(box, dtype = "int")

            box = perspective.order_points(box)
            cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)

            (tl, tr, br, bl) = box
            (tltrX, tltrY) = midpoint(tl, tr)
            (blbrX, blbrY) = midpoint(bl, br)

            # compute the midpoint between the top-left and top-right points,
            # followed by the midpoint between the top-right and bottom-right
            (tlblX, tlblY) = midpoint(tl, bl)
            (trbrX, trbrY) = midpoint(tr, br)

            # compute the Euclidean distance between the midpoints
            dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
            dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))

            # if the pixels per metric has not been initialized, then
            # compute it as the ratio of pixels to supplied metric
            # (in this case, inches)
            if dirc == 'UP':
                pixelsPerMetric = calculate_pixels_per_metric_up(height)
            elif dirc == 'DOWN':
                pixelsPerMetric = calculate_pixels_per_metric_down(height)
            # compute the size of the object
            dimA = dA / pixelsPerMetric
            dimB = dB / pixelsPerMetric
            #dim = [round(dimA,0), round(dimB,0)]

            #cv2.imshow("Image", orig)
            #cv2.waitKey(0)
            if (dimA + dimB) > sum_dim:
                #maxdim = dim
                sum_dim = dimA + dimB
                length = round(dimA,0)
                width = round(dimB,0)
                height = round(height, 0)
                if dirc == 'UP':
                    result = [130 - int(height), int(length), int(width)]
                elif dirc == 'DOWN':
                    result = [92 - int(height), int(length), int(width)]
        return result
    return [0, 0, 0]

def package_size_measure_up():
    image = camrea_img_1()
    height = IR_measure_distance()
    final = dms_counting(image, height, 'UP')
    return image, final

def package_size_measure_down():
    image = camrea_img_1()
    height = IR_measure_distance()
    final = dms_counting(image, height, 'DOWN')
    return image, final

#img, size = package_size_measure()
