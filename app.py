from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import base64
import numpy as np
import time
import cv2
import os
from gevent.pywsgi import WSGIServer

app = Flask(__name__)
CORS(app)

# construct the argument parse and parse the arguments
confthres = 0.3
nmsthres = 0.1


def get_labels(labels_path):
    # load the COCO class labels our YOLO model was trained on
    lpath = os.path.sep.join([yolo_path, labels_path])

    LABELS = open(lpath).read().strip().split("\n")
    return LABELS


def get_weights(weights_path):
    # derive the paths to the YOLO weights and model configuration
    weightsPath = os.path.sep.join([yolo_path, weights_path])
    return weightsPath


def get_config(config_path):
    configPath = os.path.sep.join([yolo_path, config_path])
    return configPath


def load_model(configpath, weightspath):
    # load our YOLO object detector trained on COCO dataset (80 classes)
    print("[INFO] loading YOLO from disk...")
    net = cv2.dnn.readNetFromDarknet(configpath, weightspath)
    return net


def do_prediction(image, net, LABELS):

    (H, W) = image.shape[:2]
    # determine only the *output* layer names that we need from YOLO
    ln = net.getLayerNames()
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

    # construct a blob from the input image and then perform a forward
    # pass of the YOLO object detector, giving us our bounding boxes and
    # associated probabilities
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    # print(layerOutputs)
    end = time.time()

    # show timing information on YOLO
    print("[INFO] YOLO took {:.6f} seconds".format(end - start))

    # initialize our lists of detected bounding boxes, confidences, and
    # class IDs, respectively
    boxes = []
    confidences = []
    classIDs = []

    # loop over each of the layer outputs
    for output in layerOutputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability) of
            # the current object detection
            scores = detection[5:]
            # print(scores)
            classID = np.argmax(scores)
            # print(classID)
            confidence = scores[classID]

            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > confthres:
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update our list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])

                confidences.append(float(confidence))
                classIDs.append(classID)

    # apply non-maxima suppression to suppress weak, overlapping bounding boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, confthres,
                            nmsthres)

    # TODO Prepare the output as required to the assignment specification
    # ensure at least one detection exists
    results = []
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            print("detected item:{}, accuracy:{}, X:{}, Y:{}, width:{}, height:{}".format(LABELS[classIDs[i]],
                                                                                          confidences[i],
                                                                                          boxes[i][0],
                                                                                          boxes[i][1],
                                                                                          boxes[i][2],
                                                                                          boxes[i][3]))
            data = {
                "label": LABELS[classIDs[i]],
                "accuracy": float(confidences[i]),
                "rectangle": {
                    "left": int(boxes[i][0]),
                    "top": int(boxes[i][1]),
                    "width": int(boxes[i][2]),
                    "height": int(boxes[i][3])
                }
            }
            results.append(data)
    return results


# argument
# if len(sys.argv) != 3:
#     raise ValueError("Argument list is wrong. Please use the following format:  {} {} {}".
#                      format("python iWebLens_server.py", "<yolo_config_folder>", "<Image file path>"))

# yolo_path = str(sys.argv[1])
yolo_path = 'yolo_tiny_configs'

# Yolov3-tiny versrion
labelsPath = "coco.names"
cfgpath = "yolov3-tiny.cfg"
wpath = "yolov3-tiny.weights"

Lables = get_labels(labelsPath)
CFG = get_config(cfgpath)
Weights = get_weights(wpath)
nets = load_model(CFG, Weights)


@app.route('/api/object_detection', methods=['POST'])
def detect():
    if request.method == 'POST':
        # Parse the data in the request body
        data = request.get_json()
        if data is None or 'image' not in data:
            return jsonify({'error': 'Invalid request'}), 400

        image_data = data['image']
        # Get UUID, default to 'Undefined' if not
        image_id = data.get('id', 'Undefined')

        # Converts Base64 encoded images to a format available to OpenCV
        decoded_image = base64.b64decode(image_data)
        np_image = np.frombuffer(decoded_image, np.uint8)
        image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

        # Call the do_prediction function to process the image
        results = do_prediction(image, nets, Lables)

        # return the result of object detection
        return jsonify({"objects": results, "id": image_id})


@app.route('/index')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    http_server = WSGIServer(("0.0.0.0", 5000), app)
    http_server.serve_forever()
