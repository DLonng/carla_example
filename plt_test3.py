import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import random

class ImageVisualizer:
    def __init__(self):
        # 打开交互模式
        plt.ion()
        
        # 创建图像窗口
        self.fig, self.axs = plt.subplots(2, 2, figsize=(20, 10))
        
    def vis_images(self, images):
        """
        在窗口中同时显示四张图像。
        
        参数：
        images：包含四个图像数组的列表。
        """
        # 遍历图像列表
        for i in range(4):
            # 清除当前子图
            self.axs[i//2, i%2].cla()
            
            # 显示图像
            self.axs[i//2, i%2].imshow(images[i])
            self.axs[i//2, i%2].axis('off')  # 可选：关闭坐标轴标签和刻度

            self.axs[i//2, i%2].set_aspect('equal')  # 可根据需要调整子图的宽高比例
        

        plt.tight_layout() # 自动调整子图布局，防止重叠
        plt.draw()         # 刷新图像窗口
        
    def close(self):
        # 关闭交互模式
        plt.ioff()
        
        # 关闭图像窗口
        plt.close(self.fig)

# 示例用法
image_visualizer = ImageVisualizer()
image1 = mpimg.imread('./1.png')
image2 = mpimg.imread('./2.png')
image3 = mpimg.imread('./3.png')
image4 = mpimg.imread('./4.jpg')
images = [image1, image2, image3, image4]

while True:
    random.shuffle(images)  # 随机打乱图像顺序
    image_visualizer.vis_images(images)
    plt.pause(1)

# 在需要停止时使用 Ctrl+C 终止循环
