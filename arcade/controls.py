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
            ("M", "MUSIC ON OR OFF (OR CLICK MUSIC)"),
        ],
    },
    {
        "key": "uno",
        "label": "UNO",
        "goal": "MATCH THE COLOUR OR THE SYMBOL ON THE TABLE. THE FIRST PLAYER WITH NO CARDS WINS.",
        "rows": [
            ("LEFT RIGHT", "CHOOSE A CARD (OR A WILD'S COLOUR)"),
            ("SPACE / CLICK", "PLAY THE GLOWING CARD"),
            ("ENTER / X", "PLAY / CANCEL THE PICKED CARDS"),
            ("D / P", "DRAW A CARD / PASS AFTER DRAWING"),
            ("U", "SAY UNO!"),
            ("ENTER / A", "AT THE END: ROOM / PLAY AGAIN"),
            ("ESC", "PAUSE"),
        ],
    },
    {
        "key": "checkers",
        "label": "CHECKERS",
        "goal": "YOU ARE RED AND MOVE FIRST. CAPTURES ARE MANDATORY. TAKE OR BLOCK ALL ENEMY PIECES.",
        "rows": [
            ("ARROWS", "MOVE THE BLUE CURSOR"),
            ("SPACE / CLICK", "PICK A RED PIECE"),
            ("SPACE / CLICK", "MOVE IT TO A LIT SQUARE"),
            ("ENTER / A", "AT THE END: ROOM / PLAY AGAIN"),
            ("ESC", "PAUSE"),
        ],
    },
    {
        "key": "connect4",
        "label": "CONNECT 4",
        "goal": "YOU ARE RED AND PLAY FIRST. GET FOUR IN A ROW: ACROSS, UP OR DIAGONAL.",
        "rows": [
            ("LEFT RIGHT", "CHOOSE A COLUMN"),
            ("SPACE / CLICK", "DROP YOUR DISC IN IT"),
            ("1 - 7", "DROP IN THAT COLUMN"),
            ("ENTER / A", "AT THE END: ROOM / PLAY AGAIN"),
            ("ESC", "PAUSE"),
        ],
    },
]

TAB_KEYS = [tab["key"] for tab in TABS]
