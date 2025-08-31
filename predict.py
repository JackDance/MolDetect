import torch
from rxnscribe import MolDetect
from huggingface_hub import hf_hub_download

# ckpt_path = hf_hub_download("Ozymandias314/MolDetectCkpt", "coref_best_hf.ckpt")
ckpt_path = "models/best_hf.ckpt"
model = MolDetect(ckpt_path, device=torch.device('cpu'), coref = True)

image_file = "/Users/luyaozhang/Downloads/translation/包含表格的图片/带有化学结构式图的表格/表格-化学结构式1.png"

# 执行化学结构图检测
predictions = model.predict_image_file(image_file, coref = True)


# 打印预测结果
print("=== Prediction Results ===")
print(f"Image file: {image_file}")
print(f"Predictions: {predictions}")
print("==========================")