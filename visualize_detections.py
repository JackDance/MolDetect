#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化MolDetect检测结果的脚本
在原始图片上绘制检测框、类别标签和置信度
"""

import cv2
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免显示问题
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
from pathlib import Path

def visualize_detections(image_path, predictions, output_path=None, show_plot=True):
    """
    在图片上可视化检测结果
    
    Args:
        image_path (str): 输入图片路径
        predictions (dict): 预测结果字典，包含bboxes和corefs
        output_path (str, optional): 输出图片路径，如果为None则不保存
        show_plot (bool): 是否显示图片
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
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"可视化结果已保存到: {output_path}")
    
    # 关闭图形，释放内存
    plt.close()
    
    return fig

def main():
    """主函数"""
    image_path = "/Users/luyaozhang/Downloads/translation/包含表格的图片/带有化学结构式图的表格/表格-化学结构式1.png"  # 输入图片路径
    
    # 预测结果（可以直接使用你的预测结果）
    predictions = {'bboxes': [{'category': '[Mol]', 'bbox': (0.24836472552474104, 0.8839419709854928, 0.5238943429037506, 0.9549774887443722), 'category_id': 1, 'score': 2011}, {'category': '[Mol]', 'bbox': (0.27358926796084754, 0.776888444222111, 0.49866980046764414, 0.8454227113556778), 'category_id': 1, 'score': 2011}, {'category': '[Mol]', 'bbox': (0.27358926796084754, 0.5107553776888444, 0.5109586801160036, 0.6233116558279139), 'category_id': 1, 'score': 2011}, {'category': '[Mol]', 'bbox': (0.27358926796084754, 0.40370185092546274, 0.49737623418886945, 0.47873936968484243), 'category_id': 1, 'score': 2011}, {'category': '[Mol]', 'bbox': (0.27358926796084754, 0.6643321660830416, 0.49737623418886945, 0.735367683841921), 'category_id': 1, 'score': 2011}, {'category': '[Mol]', 'bbox': (0.2962266778394047, 0.29664832416208103, 0.4727984748921502, 0.3691845922961481), 'category_id': 1, 'score': 2011}], 'corefs': []}
    
    output_path = "assets/output/detection_visualization.png"  # 输出图片路径
    show_plot = True  # 是否显示图片
    
    # 检查图片文件是否存在
    if not Path(image_path).exists():
        print(f"图片文件不存在: {image_path}")
        return
    
    # 可视化
    try:
        visualize_detections(
            image_path=image_path,
            predictions=predictions,
            output_path=output_path,
            show_plot=show_plot
        )
    except Exception as e:
        print(f"可视化失败: {e}")

if __name__ == "__main__":
    main()
