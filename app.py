"""
基于FastAPI的接口服务，提供如下接口：
1. 化学结构式图检测
2. 化学结构式bbox可视化
3. 健康检查
"""
import os
import torch
import cv2
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
from pathlib import Path
from typing import Dict, List, Optional
import tempfile

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from rxnscribe import MolDetect
from logger import setup_logging, log


# 配置日志
setup_logging(
    console_level="INFO",   # 控制台日志级别
    file_level="DEBUG",     # 文件日志级别
    log_file="logs/app.log" # 日志文件路径
)

# 初始化FastAPI应用
app = FastAPI(
    title="MolDetect API",
    description="化学结构式检测和可视化API服务",
    version="1.0.0"
)

# 全局变量存储模型
model = None

class DetectionResponse(BaseModel):
    """检测响应模型"""
    success: bool
    message: str
    predictions: Optional[Dict] = None
    image_info: Optional[Dict] = None

class VisualizationResponse(BaseModel):
    """可视化响应模型"""
    success: bool
    message: str
    image_path: Optional[str] = None

def load_model():
    """加载MolDetect模型"""
    global model
    try:
        ckpt_path = "models/best_hf.ckpt"
        if not os.path.exists(ckpt_path):
            raise FileNotFoundError(f"模型文件不存在: {ckpt_path}")
        
        # 自动检测设备
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        log.info(f"使用设备: {device}")
        
        model = MolDetect(ckpt_path, device=device, coref=True)
        log.info("模型加载成功")
        return True
    except Exception as e:
        log.error(f"模型加载失败: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """应用启动时加载模型"""
    log.info("正在启动MolDetect API服务...")
    if not load_model():
        log.warning("警告: 模型加载失败，某些功能可能不可用")

@app.get("/health", summary="健康检查")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "message": "MolDetect API服务运行正常",
        "model_loaded": model is not None,
        "device": str(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
    }

@app.post("/detect", response_model=DetectionResponse, summary="化学结构式图检测")
async def detect_chemical_structures(file: UploadFile = File(...)):
    """
    化学结构式图检测接口
    
    Args:
        file: 上传的图片文件
        
    Returns:
        DetectionResponse: 检测结果
    """
    if model is None:
        raise HTTPException(status_code=500, detail="模型未加载，请检查服务状态")
    
    # 验证文件类型
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # 执行检测
        predictions = model.predict_image_file(tmp_file_path, coref=True)
        
        # 获取图片信息
        img = cv2.imread(tmp_file_path)
        height, width = img.shape[:2]
        
        # 清理临时文件
        os.unlink(tmp_file_path)
        
        return DetectionResponse(
            success=True,
            message="检测完成",
            predictions=predictions,
            image_info={
                "width": width,
                "height": height,
                "filename": file.filename,
                "content_type": file.content_type
            }
        )
        
    except Exception as e:
        # 确保清理临时文件
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")

@app.post("/visualize", response_model=VisualizationResponse, summary="化学结构式bbox可视化")
async def visualize_detections(
    file: UploadFile = File(...),
    predictions: Optional[str] = None
):
    """
    化学结构式bbox可视化接口
    
    Args:
        file: 上传的图片文件
        predictions: 检测结果JSON字符串（可选，如果不提供则先进行检测）
        
    Returns:
        VisualizationResponse: 可视化结果
    """
    if model is None:
        raise HTTPException(status_code=500, detail="模型未加载，请检查服务状态")
    
    # 验证文件类型
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    
    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # 如果没有提供预测结果，先进行检测
        if predictions is None:
            pred_results = model.predict_image_file(tmp_file_path, coref=True)
        else:
            import json
            pred_results = json.loads(predictions)
        
        # 创建输出目录
        output_dir = Path("assets/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件名
        output_filename = f"visualization_{file.filename}_{hash(tmp_file_path) % 10000}.png"
        output_path = output_dir / output_filename
        
        # 执行可视化
        visualize_detections_internal(tmp_file_path, pred_results, str(output_path))
        
        # 清理临时文件
        os.unlink(tmp_file_path)
        
        return VisualizationResponse(
            success=True,
            message="可视化完成",
            image_path=str(output_path)
        )
        
    except Exception as e:
        # 确保清理临时文件
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        
        raise HTTPException(status_code=500, detail=f"可视化失败: {str(e)}")

def visualize_detections_internal(image_path: str, predictions: Dict, output_path: str):
    """
    内部可视化函数（基于visualize_detections.py的实现）
    
    Args:
        image_path: 输入图片路径
        predictions: 预测结果字典
        output_path: 输出图片路径
    """
    # 读取图片
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图片: {image_path}")
    
    # 转换BGR到RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    height, width = img_rgb.shape[:2]
    
    # 创建matplotlib图形
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    ax.imshow(img_rgb)
    ax.set_axis_off()
    
    # 定义颜色映射
    colors = {
        '[Mol]': 'red',      # 分子结构 - 红色
        '[Idt]': 'blue',     # 标识符 - 蓝色
        '[Rct]': 'green',    # 反应物 - 绿色
        '[Pdt]': 'orange',   # 产物 - 橙色
        '[Cat]': 'purple',   # 催化剂 - 紫色
        '[Sol]': 'brown',    # 溶剂 - 棕色
        '[Tmp]': 'pink',     # 温度 - 粉色
        '[Tme]': 'cyan'      # 时间 - 青色
    }
    
    # 绘制检测框
    for i, bbox_info in enumerate(predictions['bboxes']):
        category = bbox_info['category']
        bbox = bbox_info['bbox']
        score = bbox_info['score']
        category_id = bbox_info['category_id']
        
        # 转换相对坐标到绝对坐标
        x1, y1, x2, y2 = bbox
        x1_abs = int(x1 * width)
        y1_abs = int(y1 * height)
        x2_abs = int(x2 * width)
        y2_abs = int(y2 * height)
        
        # 获取颜色
        color = colors.get(category, 'gray')
        
        # 绘制矩形框
        rect = Rectangle((x1_abs, y1_abs), x2_abs - x1_abs, y2_abs - y1_abs,
                        linewidth=2, edgecolor=color, facecolor='none')
        ax.add_patch(rect)
        
        # 添加标签文本
        label_text = f"{category} (ID:{category_id})"
        ax.text(x1_abs, y1_abs - 5, label_text, 
                fontsize=10, color=color, weight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # 添加置信度文本
        score_text = f"Score: {score}"
        ax.text(x1_abs, y2_abs + 15, score_text,
                fontsize=9, color=color, weight='bold',
                bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
        
        # 添加索引标记
        ax.text(x1_abs + 5, y1_abs + 15, f"#{i}", 
                fontsize=12, color='white', weight='bold',
                bbox=dict(boxstyle="round,pad=0.2", facecolor='black', alpha=0.7))
    
    # 绘制共指关系
    if 'corefs' in predictions and predictions['corefs']:
        for coref_group in predictions['corefs']:
            if len(coref_group) >= 2:
                # 获取第一个和最后一个bbox的中心点
                first_bbox = predictions['bboxes'][coref_group[0]]['bbox']
                last_bbox = predictions['bboxes'][coref_group[-1]]['bbox']
                
                # 计算中心点
                center1_x = int((first_bbox[0] + first_bbox[2]) / 2 * width)
                center1_y = int((first_bbox[1] + first_bbox[3]) / 2 * height)
                center2_x = int((last_bbox[0] + last_bbox[2]) / 2 * width)
                center2_y = int((last_bbox[1] + last_bbox[3]) / 2 * height)
                
                # 绘制连接线
                ax.plot([center1_x, center2_x], [center1_y, center2_y], 
                       'k--', linewidth=1, alpha=0.6)
                
                # 在连接线中点添加共指标记
                mid_x = (center1_x + center2_x) / 2
                mid_y = (center1_y + center2_y) / 2
                ax.text(mid_x, mid_y, "↔", fontsize=16, color='black', 
                       weight='bold', ha='center', va='center',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='yellow', alpha=0.8))
    
    # 设置标题
    title = f"MolDetect检测结果 - {Path(image_path).name}"
    ax.set_title(title, fontsize=16, weight='bold', pad=20)
    
    # 添加图例
    legend_elements = []
    for category, color in colors.items():
        if any(bbox['category'] == category for bbox in predictions['bboxes']):
            legend_elements.append(patches.Patch(color=color, label=category))
    
    if legend_elements:
        ax.legend(handles=legend_elements, loc='upper right', 
                 bbox_to_anchor=(1.15, 1), fontsize=10)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图片
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

@app.get("/visualize/{filename}", summary="获取可视化图片")
async def get_visualization_image(filename: str):
    """
    获取可视化结果图片
    
    Args:
        filename: 图片文件名
        
    Returns:
        FileResponse: 图片文件
    """
    output_dir = Path("assets/output")
    image_path = output_dir / filename
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="图片文件不存在")
    
    return FileResponse(image_path, media_type="image/png")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=13007)
