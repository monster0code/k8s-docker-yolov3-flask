from locust import HttpUser, task, between
import os
import base64
import json
import uuid


class InternetUser(HttpUser):
    wait_time = between(1, 2)  # Wait time between tasks performed by users

    def on_start(self):
        """
        loading and encoding all images.
        """
        self.images = self.load_and_encode_images()

    def load_and_encode_images(self):
        """
        Loads images from the specified directory, encoding them as base64 strings.
        """
        images_dir = "inputfolder"  # picture storage path object_detection_test\images
        images_paths = [os.path.join(images_dir, f) for f in os.listdir(
            images_dir) if os.path.isfile(os.path.join(images_dir, f))]
        encoded_images = []
        for image_path in images_paths:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(
                    image_file.read()).decode('utf-8')
                encoded_images.append(encoded_string)
        return encoded_images

    @task
    def upload_all_images(self):
        """
        Go through all the encoded images and send them.
        """
        for image_data in self.images:
            # Generate UUID v4 as the unique identifier for the picture
            image_id = str(uuid.uuid4())
            payload = {
                "image": image_data,
                "id": image_id
            }
            headers = {'Content-Type': 'application/json'}
            response = self.client.post(
                "", data=json.dumps(payload), headers=headers)
            print(response.text)
