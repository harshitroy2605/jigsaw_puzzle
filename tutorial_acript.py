import random
import math
import tkinter as tk
from tkinter import filedialog

import pygame
from PIL import Image, ImageDraw

WIDTH, HEIGHT = 1200, 750
ROWS = 4
SNAP_DISTANCE = 35

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Jigsaw Puzzle")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 32)


def choose_image():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(
        filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp")]
    )


def make_edges(rows, cols):
    horizontal = [[0] * cols for _ in range(rows + 1)]
    vertical = [[0] * (cols + 1) for _ in range(rows)]

    for r in range(1, rows):
        for c in range(cols):
            horizontal[r][c] = random.choice([-1, 1])

    for r in range(rows):
        for c in range(1, cols):
            vertical[r][c] = random.choice([-1, 1])

    return horizontal, vertical


def edge_points(length, depth, shape):
    if shape == 0:
        return [(0, 0), (length, 0)]

    center = length / 2
    radius = length * 0.22
    points = [(0, 0), (center - radius, 0)]

    for i in range(13):
        angle = math.pi - math.pi * i / 12
        x = center + radius * math.cos(angle)
        y = shape * depth * math.sin(angle)
        points.append((x, y))

    return points + [(center + radius, 0), (length, 0)]


def make_piece(image, x, y, w, h, top, right, bottom, left):
    margin = int(min(w, h) * 0.25)
    mask = Image.new("L", (w + margin * 2, h + margin * 2), 0)

    top_edge = edge_points(w, h * .25, top)
    right_edge = edge_points(h, w * .25, right)
    bottom_edge = edge_points(w, h * .25, bottom)
    left_edge = edge_points(h, w * .25, left)

    points = [(px + margin, py + margin) for px, py in top_edge]

    points += [
        (margin + w - py, margin + px)
        for px, py in right_edge[1:]
    ]

    points += [
        (margin + w - px, margin + h - py)
        for px, py in bottom_edge[1:]
    ]

    points += [
        (margin + py, margin + h - px)
        for px, py in left_edge[1:]
    ]

    ImageDraw.Draw(mask).polygon(points, fill=255)

    piece = Image.new("RGBA", mask.size)
    piece.paste(image.crop((x, y, x + w, y + h)), (margin, margin))



    
    piece.putalpha(mask)

    return piece, margin


def create_puzzle(path):
    original = Image.open(path).convert("RGB")

    # Resize while keeping the image's original aspect ratio.
    puzzle_w = 600
    puzzle_h = int(puzzle_w * original.height / original.width)

    if puzzle_h > 560:
        puzzle_h = 560
        puzzle_w = int(puzzle_h * original.width / original.height)

    cols = max(3, round(ROWS * puzzle_w / puzzle_h))

    cell_w = puzzle_w // cols
    cell_h = puzzle_h // ROWS
    puzzle_w = cell_w * cols
    puzzle_h = cell_h * ROWS

    image = original.resize((puzzle_w, puzzle_h))
    horizontal, vertical = make_edges(ROWS, cols)

    board_x, board_y = 30, 100
    pieces = []

    for row in range(ROWS):
        for col in range(cols):
            x = col * cell_w
            y = row * cell_h

            top = 0 if row == 0 else -horizontal[row][col]
            right = 0 if col == cols - 1 else vertical[row][col + 1]
            bottom = 0 if row == ROWS - 1 else horizontal[row + 1][col]
            left = 0 if col == 0 else -vertical[row][col]

            surface, margin = make_piece(
                image, x, y, cell_w, cell_h,
                top, right, bottom, left
            )

            correct = pygame.Vector2(
                board_x + x - margin,
                board_y + y - margin
            )

            pieces.append({
                "surface": pygame.image.fromstring(
                    surface.tobytes(), surface.size, "RGBA"
                ),
                "correct": correct,
                "pos": pygame.Vector2(
                    random.randint(700, 1050),
                    random.randint(100, 650)
                ),
                "locked": False
            })

    random.shuffle(pieces)
    return pieces, pygame.Rect(board_x, board_y, puzzle_w, puzzle_h)


path = choose_image()

if not path:
    pygame.quit()
    raise SystemExit

pieces, board = create_puzzle(path)

dragging = None
offset = pygame.Vector2()
moves = 0
finished = False

running = True

while running:
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for piece in reversed(pieces):
                if piece["locked"]:
                    continue

                rect = piece["surface"].get_rect(topleft=piece["pos"])

                if rect.collidepoint(event.pos):
                    dragging = piece
                    offset = pygame.Vector2(event.pos) - piece["pos"]

                    pieces.remove(piece)
                    pieces.append(piece)
                    moves += 1
                    break

        elif event.type == pygame.MOUSEMOTION and dragging:
            dragging["pos"] = pygame.Vector2(event.pos) - offset

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if dragging:
                distance = dragging["pos"].distance_to(dragging["correct"])

                if distance < SNAP_DISTANCE:
                    dragging["pos"] = dragging["correct"]
                    dragging["locked"] = True

                dragging = None

                if all(piece["locked"] for piece in pieces):
                    finished = True

    screen.fill((30, 30, 35))

    pygame.draw.rect(screen, (45, 45, 50), board)
    pygame.draw.rect(screen, (100, 100, 110), board, 2)

    for piece in pieces:
        screen.blit(piece["surface"], piece["pos"])

    screen.blit(
        font.render(f"Moves: {moves}", True, "white"),
        (30, 35)
    )

    if finished:
        screen.blit(
            font.render("Puzzle Complete!", True, "lime"),
            (500, 35)
        )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
