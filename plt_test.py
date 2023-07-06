import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# 图像路径
image_path_1 = 'w2.png'
image_path_2 = 'w2.png'
image_path_3 = 'w2.png'
image_path_4 = 'w2.png'

# 加载图像
image_1 = mpimg.imread(image_path_1)
image_2 = mpimg.imread(image_path_2)
image_3 = mpimg.imread(image_path_3)
image_4 = mpimg.imread(image_path_4)

# 创建一个4x4的子图布局
fig, axs = plt.subplots(2, 2)

# 在每个子图中显示相应的图像
axs[0, 0].imshow(image_1)
axs[0, 0].axis('off')
axs[0, 0].set_title('Image 1')

axs[0, 1].imshow(image_2)
axs[0, 1].axis('off')
axs[0, 1].set_title('Image 2')

axs[1, 0].imshow(image_3)
axs[1, 0].axis('off')
axs[1, 0].set_title('Image 3')

axs[1, 1].imshow(image_4)
axs[1, 1].axis('off')
axs[1, 1].set_title('Image 4')

# 调整子图之间的间距
plt.subplots_adjust(wspace=0.0, hspace=0.0, left=0.0, bottom=0.0, right=1.0, top=1.0)

plt.show()
