import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import time

# 图像路径列表
image_paths = ['1.png', '2.png', '3.png']

# 打开交互模式
plt.ion()

# 创建一个图像窗口
fig = plt.figure()

# 遍历图像路径列表
for path in image_paths:
    # 加载图像
    image = mpimg.imread(path)
    
    # 清除之前的图像
    plt.clf()
    
    # 显示当前图像
    plt.imshow(image)
    plt.axis('off')  # 可选：关闭坐标轴标签和刻度
    
    # 刷新图像窗口
    plt.draw()
    
    # 暂停一段时间
    plt.pause(1.0)  # 间隔时间，单位为秒
    
# 关闭交互模式
# plt.ioff()

# 显示最后一张图像并保持窗口打开
# plt.show()
