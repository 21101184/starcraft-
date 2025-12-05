import pygame
import sys
import random

WIDTH, HEIGHT = 800, 600
FPS = 60

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tiny Bounce")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# 플레이어 패들
paddle_w, paddle_h = 100, 12
paddle = pygame.Rect((WIDTH - paddle_w)//2, HEIGHT - 40, paddle_w, paddle_h)
paddle_speed = 7

# 공
ball_r = 10
ball_x = WIDTH // 2
ball_y = HEIGHT // 2
ball_dx = random.choice([-4, 4])
ball_dy = -4

score = 0
game_over = False

def reset_ball():
    global ball_x, ball_y, ball_dx, ball_dy
    ball_x = WIDTH // 2
    ball_y = HEIGHT // 2
    ball_dx = random.choice([-4, 4])
    ball_dy = -4

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and game_over:
            if event.key == pygame.K_r:
                score = 0
                game_over = False
                reset_ball()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        paddle.x -= paddle_speed
    if keys[pygame.K_RIGHT]:
        paddle.x += paddle_speed
    paddle.x = max(0, min(WIDTH - paddle_w, paddle.x))

    if not game_over:
        ball_x += ball_dx
        ball_y += ball_dy

        # 벽 충돌
        if ball_x - ball_r <= 0 or ball_x + ball_r >= WIDTH:
            ball_dx *= -1
        if ball_y - ball_r <= 0:
            ball_dy *= -1

        # 패들과 충돌
        if paddle.collidepoint(ball_x, ball_y + ball_r):
            ball_dy *= -1
            score += 1
            # 약간 속도 증가
            ball_dx *= 1.05
            ball_dy *= 1.05

        # 바닥에 떨어지면 게임 오버
        if ball_y - ball_r > HEIGHT:
            game_over = True

    # 그리기
    screen.fill((30, 30, 30))
    pygame.draw.rect(screen, (200, 200, 200), paddle)
    pygame.draw.circle(screen, (255, 100, 100), (int(ball_x), int(ball_y)), ball_r)
    score_surf = font.render(f"Score: {score}", True, (230,230,230))
    screen.blit(score_surf, (10, 10))

    if game_over:
        go = font.render("Game Over! Press R to restart", True, (255, 200, 200))
        screen.blit(go, (WIDTH//2 - go.get_width()//2, HEIGHT//2 - 20))

    pygame.display.flip()
    clock.tick(FPS)