import pygame

# 初始化 Pygame
pygame.init()

# 窗口尺寸
window_width = 800
window_height = 600

# 创建主窗口
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Splitting Window")

# 创建上半部分的子表面
upper_surface = window.subsurface(pygame.Rect(0, 0, window_width, window_height // 2))

# 创建下半部分的子表面列表
num_rows = 2
num_cols = 4
cell_width = window_width // num_cols
cell_height = (window_height // 2) // num_rows

lower_surfaces = []
for row in range(num_rows):
    for col in range(num_cols):
        cell_rect = pygame.Rect(col * cell_width, window_height // 2 + row * cell_height, cell_width, cell_height)
        lower_surfaces.append(window.subsurface(cell_rect))

# 加载图片
images = []
for i in range(1, 9):
    image = pygame.image.load(f"{i}.png")
    images.append(image)

# 设置图片到对应的子表面
for idx, surface in enumerate(lower_surfaces):
    surface.blit(pygame.transform.scale(images[idx], (cell_width, cell_height)), (0, 0))

# 游戏循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 更新显示
    pygame.display.flip()

# 退出 Pygame
pygame.quit()
