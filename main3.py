import pygame
import sys
import numpy as np


# 初始化 Pygame
pygame.init()

# 窗口尺寸
window_width = 500
window_height = 400

# 创建主窗口
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Throttle and Brake Histograms")

# 油门和刹车输入，范围为0到100
throttle = 0
brake = 0

# 直方图的位置和尺寸
histogram_x = 40
histogram_y = 250
histogram_width = 30


# 加载方向盘图片
steering_wheel_image = pygame.image.load("steer.jpg")
steering_wheel_image = pygame.transform.scale(steering_wheel_image, (200, 200))

# 方向盘中心位置
wheel_center = (window_width // 2, window_height // 2)
angle = 0

# 创建字体对象
font = pygame.font.Font(None, 25)

# 游戏循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 清空屏幕
    window.fill((255, 255, 255))

    # 绘制油门直方图
    throttle_height = throttle * 100
    throttle_rect = pygame.Rect(histogram_x, histogram_y - throttle_height, histogram_width, throttle_height)
    pygame.draw.rect(window, (0, 255, 0), throttle_rect)

    # 绘制刹车直方图
    brake_height = brake * 100
    brake_rect = pygame.Rect(window_width - 50 - histogram_width, histogram_y - brake_height, histogram_width, brake_height)
    pygame.draw.rect(window, (255, 0, 0), brake_rect)

    # 绘制 "throttle" 和 "brake" 文字
    throttle_text = font.render("throttle", True, (0, 0, 0))
    brake_text = font.render("brake", True, (0, 0, 0))
    window.blit(throttle_text, (histogram_x, histogram_y + 10))
    window.blit(brake_text, (window_width - 50 - histogram_width, histogram_y + 10))

    # 旋转方向盘图片
    rotated_steering_wheel = pygame.transform.rotate(steering_wheel_image, angle)
    rotated_rect = rotated_steering_wheel.get_rect(center=wheel_center)

    # 绘制旋转后的方向盘图片
    window.blit(rotated_steering_wheel, rotated_rect)

    angle = np.random.uniform(0.0, 180.0)
    throttle = np.random.uniform(0.0, 1.0)
    brake = np.random.uniform(0.0, 1.0)

    # 更新显示
    pygame.display.flip()

    # 控制帧率
    pygame.time.Clock().tick(10)

# 退出 Pygame
pygame.quit()
sys.exit()
