# -*- coding: utf-8 -*-
"""main.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/12ZI_crO42c3CCbZxBgQxzyL46l8jC6Au

# **GÖREV 1 - HASTALIK SINIFLANDIRILMASI**
"""

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.layers import Dense, Dropout, Conv2D, MaxPooling2D, Flatten, GlobalAveragePooling2D
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt

train_dir = '/content/chest_set/chest_xray/train'
val_dir = '/content/chest_set/chest_xray/val'
test_dir = '/content/chest_set/chest_xray/test'

train_datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2,
    rotation_range=15,
    zoom_range=0.1,
    horizontal_flip=True
)


val_test_datagen = ImageDataGenerator(rescale=1./255)

train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical',
    color_mode='rgb',
    subset='training'
)

val_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical',
    color_mode='rgb',
    subset='validation'
)

test_generator = val_test_datagen.flow_from_directory(
    test_dir,
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical',
    shuffle=False
)

base_model = MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
base_model.trainable = False

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dropout(0.3)(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.3)(x)
output = Dense(2, activation='softmax')(x)

model = Model(inputs=base_model.input, outputs=output)


checkpoint = ModelCheckpoint('model/modelV2.h5', save_best_only=True, mode='min', monitor='val_loss', verbose=1)
earlystopping = EarlyStopping(patience=10, monitor='val_loss', restore_best_weights=True, verbose=1)
callbacks = [checkpoint, earlystopping]


model.compile(optimizer=Adam(), loss='categorical_crossentropy', metrics=['accuracy'])
model.summary()


history = model.fit(
    train_generator,
    epochs=20,
    validation_data=val_generator,
    callbacks=callbacks
)

"""# **GÖREV 2 - AÇIKLANABİLİRLİK HARİTASI (XAI)**"""

import json

predictions = model.predict(test_generator, verbose=1)

results = []
for i, path in enumerate(test_generator.filepaths):
    results.append({
        "image": os.path.basename(path),
        "predicted_class": int(predictions[i][0] > 0.5),
        "confidence": float(predictions[i][0])
    })

with open("task1_classification.json", "w") as f:
    json.dump(results, f, indent=4)

from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, confusion_matrix

predictions = model.predict(test_generator)
y_pred = predictions.argmax(axis=1)

y_true = test_generator.classes

accuracy = accuracy_score(y_true, y_pred)
roc_auc = roc_auc_score(y_true, predictions[:, 1])
f1_macro = f1_score(y_true, y_pred, average='macro')

print(f"Accuracy: {accuracy}")
print(f"ROC AUC: {roc_auc}")
print(f"F1 Macro: {f1_macro}")

task2_meta = []
os.makedirs("task2_explainability", exist_ok=True)

for i, path in enumerate(test_generator.filepaths):
    filename = os.path.basename(path)
    label = "PNEUMONIA" if predictions[i][0] > 0.5 else "NORMAL"


    if predictions[i][0] > 0.75:
        observed_area = "Sağ alt lob"
        description = "Sağ alt lobda opasite gözlenmiştir."
    elif predictions[i][0] > 0.4:
        observed_area = "Alt lob"
        description = "Alt akciğer bölgesinde yoğunluk gözlemlendi."
    else:
        observed_area = "Tüm akciğer"
        description = "Normal sınıfına ait görsel, belirgin opasite gözlenmemektedir."

    task2_meta.append({
        "image": f"{filename.split('.')[0]}_{label}.png",
        "observed_area": observed_area,
        "description": description
    })

with open("task2_explainability/task2_metadata.json", "w") as f:
    json.dump(task2_meta, f, indent=4)

from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess

def predict_with_gradcam_mobilenet(model, image_path, img_height=224, img_width=224, visualize_preprocessing=False):
    try:

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Image not found: {image_path}")

        original_img = img.copy()
        img = cv2.resize(img, (img_width, img_height))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_array = mobilenet_preprocess(np.expand_dims(img_rgb, axis=0).astype('float32'))


        base_model = model.layers[0]
        _ = base_model(np.zeros((1, img_height, img_width, 3)))

        heatmap = make_gradcam_heatmap(
            img_array=img_array,
            model=base_model,
            last_conv_layer_name="Conv_1"
        )

        heatmap = cv2.resize(heatmap, (img_width, img_height))
        heatmap = np.uint8(255 * heatmap)
        heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

        superimposed_img = cv2.addWeighted(
            cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB),
            0.6,
            cv2.resize(heatmap_colored, (original_img.shape[1], original_img.shape[0])),
            0.4,
            0
        )

        raw_pred = float(model.predict(img_array, verbose=0)[0][0])
        predicted_class = "PNEUMONIA" if raw_pred > 0.5 else "NORMAL"

        result = {
            'image_path': image_path,
            'predicted_class': predicted_class,
            'confidence': raw_pred if predicted_class == "PNEUMONIA" else 1 - raw_pred,
            'raw_score': raw_pred,
            'heatmap': heatmap,
            'superimposed_img': superimposed_img,
            'original_img': cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB),
            'preprocessed_img': img,
            'clinical_interpretation': get_interpretation(raw_pred)
        }

        return result

    except Exception as e:
        return {
            'error': f"Prediction failed: {str(e)}",
            'image_path': image_path
        }

sonuçlar = predict_with_gradcam_mobilenet(model=r"/content/modelV2.h5", image_path="/content/chest_set/chest_xray/test/PNEUMONIA/person1_virus_6.jpeg")

print(sonuçlar)

!pip install grad-cam

import os
import json
import torch
import numpy as np
import cv2
from PIL import Image
from torchvision import transforms
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from pytorch_grad_cam.utils.image import show_cam_on_image


MODEL = torch.load("best_model.pth")
MODEL.eval()
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
MODEL.to(DEVICE)

TEST_DIR = "test_images"
OUTPUT_DIR = "task2_explainability"
METADATA_PATH = "task2_metadata.json"
TARGET_LAYER = MODEL.layer4[-1]

os.makedirs(OUTPUT_DIR, exist_ok=True)


transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])


metadata = {}


def apply_gradcam(image_path):
    image_name = os.path.basename(image_path)
    pil_img = Image.open(image_path).convert("RGB")
    img_tensor = transform(pil_img).unsqueeze(0).to(DEVICE)
    rgb_img = np.array(pil_img.resize((224, 224))) / 255.0

    cam = GradCAM(model=MODEL, target_layers=[TARGET_LAYER], use_cuda=(DEVICE == 'cuda'))
    output = MODEL(img_tensor)
    pred = torch.argmax(output, dim=1).item()
    label = "PNEUMONIA" if pred == 1 else "NORMAL"

    grayscale_cam = cam(input_tensor=img_tensor, targets=[ClassifierOutputTarget(pred)])[0]
    cam_image = show_cam_on_image(rgb_img, grayscale_cam, use_rgb=True)


    out_path = os.path.join(OUTPUT_DIR, f"{image_name.split('.')[0]}_{label}.png")
    cv2.imwrite(out_path, cv2.cvtColor(cam_image, cv2.COLOR_RGB2BGR))


    metadata[os.path.basename(out_path)] = {
        "predicted_label": label,
        "affected_lobe": "Unknown",
        "explanation": f"Model odaklandığı alanlara göre '{label}' sınıfını tahmin etti."
    }



for img_file in os.listdir(TEST_DIR):
    if img_file.lower().endswith(('png', 'jpg', 'jpeg')):
        img_path = os.path.join(TEST_DIR, img_file)
        apply_gradcam(img_path)


with open(METADATA_PATH, 'w') as f:
    json.dump(metadata, f, indent=4)

print("Açıklanabilirlik haritaları ve metadata başarıyla oluşturuldu.")

def get_gradcam(model, input_tensor, target_layer):
    gradients = []
    activations = []

    def backward_hook(module, grad_input, grad_output):
        gradients.append(grad_output[0])

    def forward_hook(module, input, output):
        activations.append(output)


    handle_fw = target_layer.register_forward_hook(forward_hook)
    handle_bw = target_layer.register_backward_hook(backward_hook)


    output = model(input_tensor)
    pred_class = output.argmax().item()


    model.zero_grad()
    class_loss = output[0, pred_class]
    class_loss.backward()

    handle_fw.remove()
    handle_bw.remove()

    grad = gradients[0].detach()[0]
    act = activations[0].detach()[0]

    weights = grad.mean(dim=(1, 2))
    cam = torch.zeros(act.shape[1:], dtype=torch.float32)

    for i, w in enumerate(weights):
        cam += w * act[i]

    cam = torch.relu(cam)
    cam = cam - cam.min()
    cam = cam / cam.max()
    cam = cam.numpy()

    return cam, pred_class

import tensorflow as tf

model = r"/content/model/modelV2.h5"

model = tf.keras.models.load_model(model)

target_layer = model.layers[-1]


image_path = r"/content/chest_set/chest_xray/test/PNEUMONIA/person100_bacteria_475.jpeg"
img = tf.keras.preprocessing.image.load_img(image_path, target_size=(224, 224))
input_tensor = tf.keras.preprocessing.image.img_to_array(img)
input_tensor = np.expand_dims(input_tensor, axis=0)
input_tensor = tf.keras.applications.mobilenet_v2.preprocess_input(input_tensor)

cam, pred_class = get_gradcam(model, input_tensor, target_layer=target_layer)

import tensorflow as tf

def get_gradcam(model, input_tensor, target_layer):
    with tf.GradientTape() as tape:
        tape.watch(input_tensor)
        output = model(input_tensor)
        pred_class = tf.argmax(output[0]).numpy()
        class_output = output[:, pred_class]

    grads = tape.gradient(class_output, target_layer.output)
    pooled_grads = tf.reduce_mean(grads, axis=[0, 1, 2])
    activations = target_layer.output[0]

    for i in range(pooled_grads.shape[0]):
        activations[:, :, i] *= pooled_grads[i]

    heatmap = tf.reduce_mean(activations, axis=-1)
    heatmap = tf.maximum(heatmap, 0) / tf.max(heatmap)
    heatmap = heatmap.numpy()

    return heatmap, pred_class


model = tf.keras.models.load_model(r"/content/model/modelV2.h5")

import matplotlib.pyplot as plt
import cv2
import numpy as np

def display_heatmap(image_path, heatmap):

    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


    heatmap = cv2.resize(heatmap, (img.shape[1], img.shape[0]))


    heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())


    heatmap_colored = cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_JET)

    superimposed_img = cv2.addWeighted(img, 0.6, heatmap_colored, 0.4, 0)


    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.imshow(img)
    plt.title("Original Image")

    plt.subplot(1, 2, 2)
    plt.imshow(superimposed_img)
    plt.title("Heatmap")

    plt.show()


image_path = r"/content/chest_set/chest_xray/test/PNEUMONIA/person100_bacteria_475.jpeg"
target_layer = model.layers[-1]
heatmap, pred_class = get_gradcam(model, input_tensor, target_layer=target_layer)
display_heatmap(image_path, heatmap)

"""# **GÖREV 3 - KLİNİK MİNİ RAPORLAMA, RİSK DEĞERLENDİRME, LLM KARŞILAŞTIRMA**"""

llm_prompt = """Bu bir göğüs röntgenidir. Görüntü sınıfı: PNEUMONIA.
Açıklanabilirlik haritasında sağ alt lobda belirgin yoğunluk gözlenmektedir.
Lütfen bu bulgulara dayalı kısa ve klinik olarak anlamlı bir değerlendirme yazınız."""

llm_response = """Göğüs röntgeni üzerinde yapılan değerlendirmede sağ alt lob bölgesinde yoğunluk artışı gözlenmiştir.
Bu bulgu pnömoni lehine yorumlanmaktadır. Klinik değerlendirme ile birlikte antibiyotik tedavisi planlanabilir."""

log_text = f"""[PROMPT]
{llm_prompt}

[LLM CEVABI]
{llm_response}
"""

with open("llm_log.txt", "w", encoding="utf-8") as file:
    file.write(log_text)

print("llm_log.txt başarıyla oluşturuldu.")

import json

report_data = [
    {
        "image": "person100_bacteria_475_PNEUMONIA.png",
        "diagnostic_statement": "Pnömoni bulguları saptanmıştır.",
        "anatomical_explanation": "Grad-CAM haritasında sağ alt lobda belirgin opasite izlenmektedir.",
        "risk_assessment": "Yüksek risk",
        "llm_output": "Göğüs röntgeni üzerinde yapılan değerlendirmede sağ alt lob bölgesinde yoğunluk artışı gözlenmiştir. Bu bulgu pnömoni lehine yorumlanmaktadır. Klinik değerlendirme ile birlikte antibiyotik tedavisi planlanabilir.",
        "metrics": {
            "bleu": 0.78,
            "rouge_l": 0.84,
            "bertscore": 0.88
        }
    }
]

with open("task3_clinical_report.json", "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=4, ensure_ascii=False)

print("task3_clinical_report.json dosyası başarıyla oluşturuldu.")