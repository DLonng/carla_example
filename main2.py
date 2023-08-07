import pygame
import math
import numpy as np

# 初始化 Pygame
pygame.init()

# 窗口尺寸
window_width = 400
window_height = 400

# 创建主窗口
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Rotating Steering Wheel")

# 加载方向盘图片
steering_wheel_image = pygame.image.load("steer.jpg")
steering_wheel_image = pygame.transform.scale(steering_wheel_image, (200, 200))

# 方向盘中心位置
wheel_center = (window_width // 2, window_height // 2)

# 加载绿色和红色矩形
green_rect = pygame.Surface((30, 0))
green_rect.fill((0, 255, 0))

red_rect = pygame.Surface((30, 0))
red_rect.fill((255, 0, 0))

# 油门和刹车输入，范围为0到100
throttle = 0
brake = 0

# 直方图的位置和尺寸
histogram_x = 100
histogram_y = 250
histogram_width = 30

angle = 0

# 游戏循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 清空屏幕
    window.fill((255, 255, 255))

    # 旋转方向盘图片
    rotated_steering_wheel = pygame.transform.rotate(steering_wheel_image, angle)
    rotated_rect = rotated_steering_wheel.get_rect(center=wheel_center)

    # 绘制油门直方图
    throttle_height = throttle * 2
    throttle_rect = pygame.Rect(histogram_x, histogram_y - throttle_height, histogram_width, throttle_height)
    pygame.draw.rect(window, (0, 255, 0), throttle_rect)

    # 绘制刹车直方图
    brake_height = brake * 2
    brake_rect = pygame.Rect(histogram_x + histogram_width + 20, histogram_y - brake_height, histogram_width, brake_height)
    pygame.draw.rect(window, (255, 0, 0), brake_rect)

    # 绘制旋转后的方向盘图片
    window.blit(rotated_steering_wheel, rotated_rect)

    # 更新角度，使指示器动起来
    angle = np.random.uniform(0, 180)
    throttle = np.random.uniform(0, 1)
    brake = np.random.uniform(0, 1)

    # 更新显示
    pygame.display.flip()

    # 控制帧率
    pygame.time.Clock().tick(10)

# 退出 Pygame
pygame.quit()
