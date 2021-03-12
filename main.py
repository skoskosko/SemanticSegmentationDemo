#!/usr/bin/env python3
"""
Websocket server forked from https://github.com/Bronkoknorb/PyImageStream

"""


import argparse
import os
import io

import tornado.ioloop
import tornado.web
import tornado.websocket
from PIL import Image

import urllib

from matplotlib import cm

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Input, Dropout, concatenate, BatchNormalization, Activation, Conv2DTranspose
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint
from sklearn.model_selection import train_test_split
import keras.losses
import os
import numpy as np
import cv2
import matplotlib.pyplot as plt
import sys
import time
import asyncio


# initiating kears model for image detection

def dice_loss(softmax_output, labels, ignore_background=False, square=False):
    if ignore_background:
      labels = labels[..., 1:]
      softmax_output = softmax_output[..., 1:]
    axis = (0,1,2)
    eps = 1e-7
    nom = (2 * tf.reduce_sum(labels * softmax_output, axis=axis) + eps)
    if square:
      labels = tf.square(labels)
      softmax_output = tf.square(softmax_output)
    denom = tf.reduce_sum(labels, axis=axis) + tf.reduce_sum(softmax_output, axis=axis) + eps
    return 1 - tf.reduce_mean(nom / denom)


model = tf.keras.models.load_model('./tensor_model', custom_objects={'dice_loss': dice_loss})


parser = argparse.ArgumentParser(description='Start the SematicSegmentationDemo server.')

parser.add_argument('--port', default=8888, type=int, help='Web server port (default: 8888)')
parser.add_argument('--url', default="http://192.168.0.2:56000/jpeg", type=str, help='Get Image url')
parser.add_argument('--quality', default=70, type=int, help='JPEG Quality 1 (worst) to 100 (best) (default: 70)')
parser.add_argument('--snippet', default=2, type=int, help='Snippet length in seconds')

args = parser.parse_args()

# Camera class for fetching images

class Camera:

    def __init__(self, url, quality, snippet):
        self.camera_domain = url
        self.quality = quality
        self.snippet = snippet
        print("Camera initialized")

    def get_jpeg_image_bytes(self):

        start = time.time()

        pred_images = []
        pred_times = []

        # while(True):
        start_gather = time.time()
        with urllib.request.urlopen(self.camera_domain) as url:
            resp = url.read()

        image = np.asarray(bytearray(resp), dtype="uint8")
        img = cv2.imdecode(image, 0)

        DIM = (512, 512)

        img = cv2.resize(img, DIM)

        img = img/255.
        pred_images.append( np.array(img) )

        end_gather = time.time()

        pred_times.append(end_gather - start_gather)
            # if (end_gather - start) > self.snippet:
            #     break

        pred_images = np.array(pred_images)

        end_gather = time.time()

        print("Total frames ", len(pred_images))
        print("Capture time ", end_gather - start)

        predicted = model.predict(pred_images)

        response = []
        for i in range(0, len(predicted)):

            np_img = np.squeeze( predicted[i]*255. , axis=2)
            pimg = Image.fromarray(np_img).convert('RGB')

            with io.BytesIO() as bytesIO:
                pimg.save(bytesIO, "JPEG", quality=self.quality, optimize=True)
                response.append(bytesIO.getvalue())
        end = time.time()
        print("Total time ", end - start)
        return response, pred_times

camera = Camera(args.url, args.quality, args.snippet)


class ImageWebSocket(tornado.websocket.WebSocketHandler):
    clients = set()

    def check_origin(self, origin):
        # Allow access from every origin
        return True

    def open(self):
        ImageWebSocket.clients.add(self)
        print("WebSocket opened from: " + self.request.remote_ip)

    # when message is recieved, take images and send them back
    def on_message(self, message):
        print(message)
        jpeg_bytes, times = camera.get_jpeg_image_bytes()
        self.write_message(jpeg_bytes[0], binary=True)
        
        # for i in range(0, len(jpeg_bytes)):
        #     start = time.time()
        #     self.write_message(jpeg_bytes[i], binary=True)
        #     end = time.time()
        #     time.sleep(times[i] - (end-start) )

        
    def on_close(self):
        ImageWebSocket.clients.remove(self)
        print("WebSocket closed from: " + self.request.remote_ip)


script_path = os.path.dirname(os.path.realpath(__file__))
static_path = script_path + '/static/'

app = tornado.web.Application([
        (r"/websocket", ImageWebSocket),
        (r"/(.*)", tornado.web.StaticFileHandler, {'path': static_path, 'default_filename': 'index.html'}),
    ])
app.listen(args.port)

print("Starting server: http://localhost:" + str(args.port) + "/")

tornado.ioloop.IOLoop.current().start()
