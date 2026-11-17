"""Numbers and settings shared by the whole game.

Change values here instead of hunting for them inside the screens.
"""

GAME_TITLE = "ARCADE MASTERS"

# Every picture is painted on a small canvas and blown up 3x, which is what
# gives the game its chunky pixel-art look.
BASE_W, BASE_H, SCALE = 320, 180, 3
SCREEN_W, SCREEN_H = BASE_W * SCALE, BASE_H * SCALE

# Rewards
CHAMPIONSHIP_PRIZE = 50
POINTS_WIN = 2
POINTS_TIE = 1

# Store prices by rarity
PRICES = {"common": 20, "rare": 100, "legendary": 500}
RARITIES = ["legendary", "rare", "common"]
SLOTS = ["hair", "shirt", "name"]
SLOT_LABELS = {"hair": "Hair", "shirt": "Shirt", "name": "Name"}

# Games
GAMES = ["uno", "checkers", "connect4"]
GAME_LABELS = {"uno": "UNO", "checkers": "CHECKERS", "connect4": "CONNECT FOUR"}
BOTS_PER_GAME = {"uno": 3, "checkers": 1, "connect4": 1}
CHAMPIONSHIP_BOTS = 3

# Bot levels. Each bot has one (see bots.py). Beating a bot pays its level's coins; in UNO, where you play
# three bots, you get the average of their three levels.
LEVELS = ["easy", "medium", "hard", "expert"]
LEVEL_COINS = {"easy": 5, "medium": 15, "hard": 25, "expert": 40}

# How each level plays. UNO: chances between 0 and 1 (see UnoGame.bot_turn).
UNO_LEVELS = {
    "easy": {"twins": 0.1, "stack": 0.15, "smart": 0.15, "forget_uno": 0.5},
    "medium": {"twins": 0.35, "stack": 0.5, "smart": 0.6, "forget_uno": 0.25},
    "hard": {"twins": 0.75, "stack": 0.85, "smart": 0.9, "forget_uno": 0.1},
    "expert": {"twins": 1.0, "stack": 1.0, "smart": 1.0, "forget_uno": 0.0},
}
# Checkers and Connect Four: (how many moves the bot looks ahead, chance of a random move)
CHECKERS_LEVELS = {"easy": (1, 0.5), "medium": (2, 0.25), "hard": (3, 0.08), "expert": (5, 0.0)}
CONNECT4_LEVELS = {"easy": (1, 0.5), "medium": (2, 0.2), "hard": (4, 0.08), "expert": (5, 0.0)}
SIMULATED_TIE_CHANCE = 0.1  # bot-versus-bot Connect Four in the championship

# Player name rules
NAME_MIN, NAME_MAX = 1, 10

# Animation (set ANIMATIONS to False to make every screen change instant)
ANIMATIONS = True
FRAME_DELAY = 0.045
# Bots think for a random time between these two numbers of seconds before each move
BOT_THINK = (1.0, 3.0)

# The player has this many seconds for each turn at every table. When time runs out the game plays
# for them: in UNO they draw and the turn passes, in checkers and Connect Four a random move is made.
TURN_SECONDS = 15

# Fade to black between screens (task A1): frames down to black (and the same back up), and the time per frame
FADE_STEPS = 5
FADE_DELAY = 0.035

# Bots shuffle and turn while idle (task A4): seconds between two idle moments in the room
IDLE_EVERY = 1.2

# Soft neon glow around bright colours on every picture (visual update, idea 2). Costs about 20 ms a picture.
GLOW = True

# Font for all text painted on the pictures (visual update, idea 4): a file in arcade/art/fonts/,
# or None for the old built-in 5x7 font
TEXT_FONT = "Jersey10-Regular.ttf"

# Title screen animation (visual update, idea 5): seconds between two frames
TITLE_EVERY = 0.4
