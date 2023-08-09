import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.transforms as transforms
import numpy as np
from PIL import Image

# 创建一个图表和一个子坐标系
fig, ax = plt.subplots(figsize=(8, 6))

# 方向盘的角度
steer = 0  # 输入的角度，范围为[-1.0, 1.0]

# 将输入角度转换为旋转角度
rotate_angle = steer * 90

# 加载方向盘图片
img = mpimg.imread('steer.jpg')  # 请替换为实际图片文件的路径
# 缩小方向盘图片的宽度和高度为原来的一半
img = Image.fromarray(img)  # 将 NumPy 数组转换为 PIL 图像
img = img.resize((img.width // 2, img.height // 2))  # 缩放图片尺寸

# 缩小方向盘图片的宽度和高度为原来的一半
img_width = img.width
img_height = img.height

# 创建旋转变换对象，并设置旋转中心为图片中心
rotate_transform = transforms.Affine2D().rotate_deg_around(img_width / 2, img_height / 2, rotate_angle)

# 在坐标系中绘制方向盘图片
img_plot = ax.imshow(img, extent=[0, img_width // 2, 0, img_height // 2], transform=rotate_transform + ax.transData)

# 绘制垂直进度条表示刹车和油门
brake = 50  # 刹车百分比
throttle = 50  # 油门百分比
ax.bar(10, brake, color='red', width=20)
ax.bar(30, throttle, color='green', width=20)

# 设置标题和标签
ax.set_title("Steering Wheel, Brake, and Throttle")
ax.set_xlabel('Percentage')

# 调整子坐标系的布局
# plt.tight_layout()

# 显示图形
plt.show()
