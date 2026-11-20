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
UNO_CHAMP_POINTS = {1: 2, 2: 1}  # the championship's UNO round is played to the last player: 1st 2 points, 2nd 1

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
# UNO is played until one player is left: the share of the prize each place wins (last place wins nothing).
UNO_PLACE_SHARE = {1: 1.0, 2: 0.5, 3: 0.25}

# How each level plays. UNO: chances between 0 and 1 (see UnoGame.bot_turn).
UNO_LEVELS = {
    "easy": {"twins": 0.0, "stack": 0.0, "smart": 0.0, "forget_uno": 0.7},
    "medium": {"twins": 0.2, "stack": 0.3, "smart": 0.35, "forget_uno": 0.4},
    "hard": {"twins": 0.75, "stack": 0.85, "smart": 0.9, "forget_uno": 0.1},
    "expert": {"twins": 1.0, "stack": 1.0, "smart": 1.0, "forget_uno": 0.0},
}
# Checkers and Connect Four: depth = how many moves the bot looks ahead, blunder = chance of a random move.
# Connect Four also: win / block = chance the bot notices a four it can make now / one it must stop.
CHECKERS_LEVELS = {
    "easy": {"depth": 0, "blunder": 0.5},
    "medium": {"depth": 1, "blunder": 0.5},
    "hard": {"depth": 3, "blunder": 0.08},
    "expert": {"depth": 5, "blunder": 0.0},
}
CONNECT4_LEVELS = {
    "easy": {"depth": 0, "blunder": 0.85, "win": 0.4, "block": 0.15},
    "medium": {"depth": 1, "blunder": 0.5, "win": 0.9, "block": 0.55},
    "hard": {"depth": 4, "blunder": 0.08, "win": 1.0, "block": 1.0},
    "expert": {"depth": 5, "blunder": 0.0, "win": 1.0, "block": 1.0},
}
SIMULATED_TIE_CHANCE = 0.1  # bot-versus-bot Connect Four in the championship

# Player name rules
NAME_MIN, NAME_MAX = 1, 10

# Animation (set ANIMATIONS to False to make every screen change instant)
ANIMATIONS = True
FRAME_DELAY = 0.045
# Bots think for a random time between these two numbers of seconds before each move
# Corta UNO (arcade/logic/trivia.py), for each bot level:
#   cut     the chance the bot tries to cut the player's UNO, and react: how fast it presses (seconds after the UNO
#           button appears; the player has UNO_SECONDS to say UNO first)
#   say     how long the bot takes to say its own UNO: the time the player has to cut it
#   knows   how often it answers a question right, and think: how many seconds it takes to answer
CUT_LEVELS = {  # react: how long after the UNO button shows a bot needs to cut it (the player has UNO_SECONDS)
    "easy": {"cut": 0.25, "react": (1.7, 2.3), "say": (2.0, 2.8), "knows": 0.55, "think": (3.0, 6.5)},
    "medium": {"cut": 0.4, "react": (1.5, 2.1), "say": (1.6, 2.4), "knows": 0.7, "think": (2.5, 6.0)},
    "hard": {"cut": 0.55, "react": (1.3, 1.9), "say": (1.2, 2.0), "knows": 0.82, "think": (2.0, 5.0)},
    "expert": {"cut": 0.7, "react": (1.1, 1.7), "say": (0.9, 1.5), "knows": 0.92, "think": (1.5, 4.0)},
}
BOT_THINK = (1.0, 3.0)

# The player has this many seconds for each turn at every table. When time runs out the game plays
# for them: in UNO they draw and the turn passes, in checkers and Connect Four a random move is made.
TURN_SECONDS = 15

# Fade to black between screens (task A1): frames down to black (and the same back up), and the time per frame
FADE_STEPS = 5
FADE_DELAY = 0.035

# The bots walk about the room (arcade/wander.py): seconds between two moments when they decide what to do next
IDLE_EVERY = 1.2

# Soft neon glow around bright colours on every picture (visual update, idea 2). Costs about 20 ms a picture.
GLOW = True

# Font for all text painted on the pictures (visual update, idea 4): a file in arcade/art/fonts/,
# or None for the old built-in 5x7 font
TEXT_FONT = "Jersey10-Regular.ttf"

