import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import threading
import time
import random

class ImageVisualizer:
    def __init__(self):
        # 创建图像窗口和子图
        self.fig, self.axs = plt.subplots(2, 2)

        # 创建锁对象
        self.lock = threading.Lock()

        # 创建事件对象
        self.event = threading.Event()

    def vis_images(self, image_paths):
        """
        在窗口中同时显示四张图像。

        参数：
        image_paths：包含四个图像文件路径的列表。
        """
        # 加锁，确保同一时间只有一个线程访问图像窗口
        self.lock.acquire()

        # 遍历图像路径列表
        for i, path in enumerate(image_paths):
            # 加载图像
            image = mpimg.imread(path)

            # 清除当前子图
            self.axs[i // 2, i % 2].cla()

            # 显示当前图像
            self.axs[i // 2, i % 2].imshow(image)
            self.axs[i // 2, i % 2].axis('off')  # 可选：关闭坐标轴标签和刻度

        # 刷新图像窗口
        plt.draw()

        # 释放锁
        self.lock.release()

    def close(self):
        # 关闭图像窗口
        plt.close(self.fig)

image_visualizer = ImageVisualizer()

# 创建 ImageVisualizer 实例（在子线程中）
def create_image_visualizer():
    while True:
        # 等待主线程发出的通知
        image_visualizer.event.wait()

        # 调用 vis_images 方法显示图像
        image_visualizer.vis_images(image_paths)

        # 重置事件状态
        image_visualizer.event.clear()

# 图像路径列表
image_paths = ['1.png', '2.png', '3.png', '4.jpg']

# 创建并启动子线程
thread = threading.Thread(target=create_image_visualizer)
thread.start()

# 在主线程中每隔 1 秒通知子线程更新图像
while True:
    time.sleep(1)
    random.shuffle(image_paths)
    # 设置事件，通知子线程更新图像
    image_visualizer.event.set()

# 在需要停止时使用 Ctrl+C 终止循环

