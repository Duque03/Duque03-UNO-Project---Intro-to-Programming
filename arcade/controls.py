"""The text of the "How to play" panel (task A3): what each key or click does.

Keep it in line with the buttons of the screens and with docs/game-design.md.
Each tab: a short label, the goal in one sentence, then (key, what it does) rows.
"""

TABS = [
    {
        "key": "room",
        "label": "ROOM",
        "goal": "WALK UP TO A TABLE AND PRESS E TO PLAY. EVERY WIN EARNS COINS FOR THE STORE.",
        "rows": [
            ("W A S D", "WALK (THE ARROW KEYS WORK TOO)"),
            ("CLICK", "WALK TO THE SPOT YOU CLICKED"),
            ("E", "PLAY A TABLE OR ENTER THE STORE"),
            ("I", "CHAMPIONSHIP RULES (BY THE CUP)"),
            ("ESC", "PAUSE MENU AND WARDROBE"),
        ],
    },
    {
        "key": "uno",
        "label": "UNO",
        "goal": "MATCH THE COLOUR OR THE SYMBOL ON THE TABLE. THE FIRST PLAYER WITH NO CARDS WINS.",
        "rows": [
            ("CLICK CARD", "PLAY ONE OF YOUR GLOWING CARDS"),
            ("D", "DRAW A CARD (OR CLICK THE DECK)"),
            ("P", "PASS AFTER DRAWING"),
            ("CLICK COLOUR", "CHOOSE THE COLOUR OF A WILD"),
            ("ENTER", "BACK TO THE ROOM AT THE END"),
            ("ESC", "PAUSE"),
        ],
    },
    {
        "key": "checkers",
        "label": "CHECKERS",
        "goal": "YOU ARE RED AND MOVE FIRST. CAPTURES ARE MANDATORY. TAKE OR BLOCK ALL ENEMY PIECES.",
        "rows": [
            ("CLICK PIECE", "SELECT ONE OF YOUR RED PIECES"),
            ("CLICK SQUARE", "MOVE IT TO A LIT SQUARE"),
            ("ENTER", "BACK TO THE ROOM AT THE END"),
            ("ESC", "PAUSE"),
        ],
    },
    {
        "key": "connect4",
        "label": "CONNECT 4",
        "goal": "YOU ARE RED AND PLAY FIRST. GET FOUR IN A ROW: ACROSS, UP OR DIAGONAL.",
        "rows": [
            ("CLICK COLUMN", "DROP YOUR DISC IN IT"),
            ("ENTER", "BACK TO THE ROOM AT THE END"),
            ("ESC", "PAUSE"),
        ],
    },
]

TAB_KEYS = [tab["key"] for tab in TABS]
