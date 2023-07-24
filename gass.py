import numpy as np
import matplotlib.pyplot as plt

def generate_standard_normal_heatmap(height, width, center_x, center_y):
    x, y = np.meshgrid(np.arange(width), np.arange(height))
    distance = (x - center_x) ** 2 + (y - center_y) ** 2
    exponent = -0.5 * distance
    heatmap = np.exp(exponent)
    return heatmap

# 图像尺寸
height, width = 200, 200

# 正态分布中心位置
center_x, center_y = 100, 100

# 生成heatmap
heatmap = generate_standard_normal_heatmap(height, width, center_x, center_y)

# 显示heatmap
plt.imshow(heatmap, cmap='hot', interpolation='nearest')
plt.colorbar()
plt.title("Standard Normal Heatmap")
plt.show()
