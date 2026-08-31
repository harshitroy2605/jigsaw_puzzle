# make sure you download 3.13 or older (mine is 3.10 , i have multiple versions (   py -0p   ))






# Import random for shuffling/random positions, math for the curved jigsaw shape, and tkinter for the file picker. 
import random, math, tkinter as tk
# Import Tkinter's file-dialog helper so the user can choose an image.
from tkinter import filedialog
# Import Pygame for the window, drawing, mouse events, and game loop.
import pygame
# Import Pillow tools: Image for image processing, ImageDraw for masks, and ImageOps for padding.
from PIL import Image, ImageDraw, ImageOps

# Set the size of the Pygame window.
W, H = 1200, 750
# Use four rows; the number of columns is calculated from the image aspect ratio.
ROWS = 4
# A piece snaps into place when it is within 35 pixels of its target.
SNAP = 35

# Initialize Pygame.
pygame.init()
# Create the Pygame window.
screen = pygame.display.set_mode((W, H))
# Set the title shown on the window.
pygame.display.set_caption("Jigsaw Puzzle")
# Create a clock so we can control the game speed.
clock = pygame.time.Clock()
# Create a font used for the move counter and completion message.
font = pygame.font.Font(None, 32)

# Function that opens a file picker and returns the selected image path.
def choose_image():
# Create a small Tkinter root window because the file dialog needs one.
    root = tk.Tk()
# Hide the Tkinter window; we only want the file picker.
    root.withdraw()
# Open the file picker and return the selected filename.
    return filedialog.askopenfilename(
# Limit the picker to common image formats.
        filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp")]
# End the file-dialog call.
    )

# Create random tab/socket information for all shared puzzle edges.
def make_edges(rows, cols):
# Store horizontal boundaries; 0 means a flat outside edge initially.
    horizontal = [[0] * cols for _ in range(rows + 1)]
# Store vertical boundaries; there is one more boundary than internal gaps.
    vertical = [[0] * (cols + 1) for _ in range(rows)]
# Generate only internal horizontal edges; the outer borders stay flat.
    for r in range(1, rows):
# Generate one shared edge for every column.
        for c in range(cols):
# -1 creates a socket and +1 creates a tab.
            horizontal[r][c] = random.choice([-1, 1])
# Generate internal vertical edges for every row.
    for r in range(rows):
# Skip the outer left border and generate internal boundaries only.
        for c in range(1, cols):
# Randomly choose whether this shared edge is a tab or socket.
            vertical[r][c] = random.choice([-1, 1])
# Return both sets of edge information.
    return horizontal, vertical

# Build the points for one straight edge, tab, or socket.
def edge_points(length, depth, shape):
# A zero shape means this is an outside edge, so it must be straight.
    if shape == 0:
# Return the two endpoints of a straight edge.
        return [(0, 0), (length, 0)]
# Put the curve in the middle and make its radius proportional to the edge length.
    center, radius = length / 2, length * .22
# Start with the straight section before the curved tab/socket.
    points = [(0, 0), (center - radius, 0)]
# Use 13 points to approximate a smooth semicircle.
    for i in range(13):
# Move the angle from pi to zero to trace half a circle.
        a = math.pi - math.pi * i / 12
# Calculate the x-coordinate of the curve.
        points.append((center + radius * math.cos(a),
# Calculate the y-coordinate; shape flips the curve inward/outward.
                       shape * depth * math.sin(a)))
# Add the end of the curve and the final endpoint, then return all points.
    return points + [(center + radius, 0), (length, 0)]

# Create one puzzle piece from the source image and its four edge shapes.
def make_piece(image, x, y, w, h, top, right, bottom, left):
# Add space around the cell because tabs extend outside the normal rectangle.
    margin = int(min(w, h) * .25)
# Create a black grayscale mask; black is transparent and white will be visible.
    mask = Image.new("L", (w + 2 * margin, h + 2 * margin), 0)

# Generate the top edge shape.
    top_edge = edge_points(w, h * .25, top)
# Generate the right edge shape; its length is the cell height.
    right_edge = edge_points(h, w * .25, right)
# Generate the bottom edge shape.
    bottom_edge = edge_points(w, h * .25, bottom)
# Generate the left edge shape.
    left_edge = edge_points(h, w * .25, left)

# Start the polygon with the top edge and shift it by the margin.
    points = [(px + margin, py + margin) for px, py in top_edge]
# Transform the horizontal edge points so the right edge becomes vertical.
    points += [(margin + w - py, margin + px)
# Skip the first point because that corner was already added by the previous edge.
               for px, py in right_edge[1:]]
# Transform points for the bottom edge.
    points += [(margin + w - px, margin + h - py)
# Again skip the shared corner point.
               for px, py in bottom_edge[1:]]
# Transform points for the left edge to close the shape.
    points += [(margin + py, margin + h - px)
# Skip the already-used corner.
               for px, py in left_edge[1:]]

# Fill the jigsaw polygon white so this part of the image will remain visible.
    ImageDraw.Draw(mask).polygon(points, fill=255)

# This line performs the operation shown below.
    # IMPORTANT: include the surrounding image pixels in the piece.
# This line performs the operation shown below.
    # The old code pasted only the rectangular cell, so tabs/sockets
# This line performs the operation shown below.
    # contained transparent pixels and appeared black.
# Add surrounding image space so the tab/socket area contains real image pixels.
    padded = ImageOps.expand(image, border=margin, fill=(0, 0, 0))
# Crop the enlarged piece area and convert it to RGBA so it can use transparency.
    piece = padded.crop((x, y, x + w + 2 * margin, y + h + 2 * margin)).convert("RGBA")
# Use the jigsaw mask as the alpha channel: outside the shape becomes transparent.
    piece.putalpha(mask)

# Return the finished piece and its margin.
    return piece, margin

# Load the selected image and generate every puzzle piece plus its target board.
def create_puzzle(path):
# Open the image and convert it to standard RGB.
    original = Image.open(path).convert("RGB")

# Start with a puzzle width of 600 pixels.
    pw = 600
# Calculate height from the original aspect ratio so the image is not distorted.
    ph = int(pw * original.height / original.width)
# If the calculated height is too large for the window...
    if ph > 560:
# Limit the puzzle height.
        ph = 560
# Recalculate width while preserving the original aspect ratio.
        pw = int(ph * original.width / original.height)

# Calculate columns from the image shape, with at least three columns.
    cols = max(3, round(ROWS * pw / ph))
# Calculate the width and height of each rectangular grid cell.
    cw, ch = pw // cols, ph // ROWS
# Adjust total dimensions so they divide perfectly into the grid.
    pw, ph = cw * cols, ch * ROWS
# Resize the original image to the final puzzle dimensions.
    image = original.resize((pw, ph))

# Generate the random shared tab/socket information.
    horizontal, vertical = make_edges(ROWS, cols)
# Set the top-left position of the completed puzzle on the screen.
    board_x, board_y = 30, 100
# Create a list that will hold every generated puzzle piece.
    pieces = []

# Loop through each puzzle row.
    for row in range(ROWS):
# Loop through each puzzle column.
        for col in range(cols):
# Find this cell's top-left position inside the image.
            x, y = col * cw, row * ch

# First row gets a flat top; otherwise use the opposite of the shared edge.
            top = 0 if row == 0 else -horizontal[row][col]
# Last column gets a flat right edge; otherwise use the shared vertical edge.
            right = 0 if col == cols - 1 else vertical[row][col + 1]
# Last row gets a flat bottom; otherwise use the shared horizontal edge.
            bottom = 0 if row == ROWS - 1 else horizontal[row + 1][col]
# First column gets a flat left edge; otherwise use the opposite shared edge.
            left = 0 if col == 0 else -vertical[row][col]

# Create the actual jigsaw-shaped image for this cell.
            surface, margin = make_piece(
# Pass the image, cell position/size, and four edge shapes.
                image, x, y, cw, ch, top, right, bottom, left
# Finish the target position calculation.
            )

# Store the exact screen position where this piece belongs.
            correct = pygame.Vector2(
# Convert the image x-position to the screen position and account for the margin.
                board_x + x - margin,
# Do the same for the y-position.
                board_y + y - margin
# Finish the target position calculation.
            )

# Add this piece and all information needed to interact with it.
            pieces.append({
# Convert the Pillow image into a Pygame surface.
                "surface": pygame.image.fromstring(
# Give Pygame the raw RGBA bytes, dimensions, and pixel format.
                    surface.tobytes(), surface.size, "RGBA"
# Finish the random position.
                ),
# Save the solved position.
                "correct": correct,
# Give the piece a random starting position on the right side.
                "pos": pygame.Vector2(
# Random x-coordinate in the pieces area.
                    random.randint(700, 1050),
# Random y-coordinate in the pieces area.
                    random.randint(100, 650)
# Finish the random position.
                ),
# The piece starts unsolved, so it can be dragged.
                "locked": False
# Finish the piece dictionary and add it to the list.
            })

# Shuffle the list so the pieces start in a random order.
    random.shuffle(pieces)
# Return the pieces and the rectangle representing the target board.
    return pieces, pygame.Rect(board_x, board_y, pw, ph)

# Ask the user to choose an image.
path = choose_image()
# If the user cancelled the file picker...
if not path:
# Cleanly shut down Pygame.
    pygame.quit()
# Stop the program immediately.
    raise SystemExit

# Generate the puzzle pieces and board from the selected image.
pieces, board = create_puzzle(path)
# No piece is being dragged at the beginning.
dragging = None
# Will store where inside the piece the mouse grabbed it.
offset = pygame.Vector2()
# Count how many pieces the user picks up.
moves = 0
# The puzzle is not solved yet.
finished = False
# This controls whether the main game loop continues.
running = True

# Keep running the game until the user closes the window.
while running:
# Read every event that happened since the last frame.
    for event in pygame.event.get():
# Detect the window close button.
        if event.type == pygame.QUIT:
# Stop the main loop.
            running = False

# Detect a left-mouse-button press.
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
# Check topmost pieces first because pieces can overlap.
            for piece in reversed(pieces):
# Ignore pieces that have already been solved.
                if piece["locked"]:
# Skip this piece and move to the next one.
                    continue
# Get the piece's rectangular collision area at its current position.
                rect = piece["surface"].get_rect(topleft=piece["pos"])
# Check whether the mouse click is inside that rectangle.
                if rect.collidepoint(event.pos):
# Remember which piece the user selected.
                    dragging = piece
# Store the exact grab offset so the piece does not jump.
                    offset = pygame.Vector2(event.pos) - piece["pos"]
# Remove it temporarily from its current list position.
                    pieces.remove(piece)
# Put it at the end so it will be drawn on top of other pieces.
                    pieces.append(piece)
# Count this pickup as one move.
                    moves += 1
# Stop searching because we found the clicked piece.
                    break

# If the mouse moves while a piece is being dragged...
        elif event.type == pygame.MOUSEMOTION and dragging:
# Move the piece while preserving the point where it was grabbed.
            dragging["pos"] = pygame.Vector2(event.pos) - offset

# Detect release of the left mouse button.
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
# Only process a drop if a piece was being dragged.
            if dragging:
# Measure distance to the target and check whether it is close enough to snap.
                if dragging["pos"].distance_to(dragging["correct"]) < SNAP:
# Put the piece exactly at its correct target position.
                    dragging["pos"] = dragging["correct"]
# Mark the piece as solved so it cannot be moved again.
                    dragging["locked"] = True
# Clear the dragging state because the mouse was released.
                dragging = None
# all() checks whether every piece is now locked.
                finished = all(piece["locked"] for piece in pieces)

# Clear the previous frame with a dark background.
    screen.fill((30, 30, 35))
# Draw the area where the completed puzzle should go.
    pygame.draw.rect(screen, (45, 45, 50), board)
# Draw a thin border around the target board.
    pygame.draw.rect(screen, (100, 100, 110), board, 2)

# Draw every puzzle piece.
    for piece in pieces:
# Copy the piece surface onto the screen at its current position.
        screen.blit(piece["surface"], piece["pos"])

# Render and display the current number of moves.
    screen.blit(font.render(f"Moves: {moves}", True, "white"), (30, 35))

# If all pieces are solved...
    if finished:
# Display the completion message.
        screen.blit(font.render("Puzzle Complete!", True, "lime"), (500, 35))

# Update the actual window with everything drawn this frame.
    pygame.display.flip()
# Limit the loop to about 60 frames per second.
    clock.tick(60)

# Cleanly shut down Pygame after the loop ends.
pygame.quit()
