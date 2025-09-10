import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model

class TrafficClassifier:

    def __init__(self):
        self.model_path = "mobilenetv2_custom.keras"
        self.img_size = (224, 224)                          
        self.class_names = ["stop sign", "traffic cone", "traffic lights", "walker"]

        self.model = load_model(self.model_path)

    def ImagePredict(self, img_path: str):
        # Load and resize the image to the model's expected size
        img = image.load_img(img_path, target_size=self.img_size)
        arr = image.img_to_array(img).astype(np.float32)
        arr = np.expand_dims(arr, axis=0)

        probs = self.model.predict(arr, verbose=0)[0]

        idx = int(np.argmax(probs))
        label = self.class_names[idx]

        return label
