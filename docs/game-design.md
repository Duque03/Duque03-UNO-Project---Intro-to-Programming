# Arcade Masters: game design

What the game must do. Tests and reviews are checked against this document.
Numbers live in `arcade/config.py`.

## 1. Title screen

- Shows the background and the name of the game in big letters.
- A big **Insert name** button opens a name field. **Play** enters the arcade.
- Names: 1 to 10 characters, letters, numbers, spaces, `-` and `_`. Stored in capitals. Anything else is rejected with a message.
- A name that has played before continues with its saved coins, cosmetics, wins and championship status.

## 2. Arcade room

- Pixel-art room seen from above. The player appears at the bottom, by the door, wearing the default clothes, with the name in a tag above the head.
- The player walks with W A S D (or arrow keys, or by clicking) and has four looks: down, up, left, right.
- Five bots, each with a unique name and look: PIXEL, TURBO, GLITCH, JOY, BYTE.
- Three game tables stand out from the scenery: UNO (left), checkers (top middle), Connect Four (right).
- The store is at the top right. The championship cabinet is at the top left.
- A coin counter is shown at the top right of the room. It is not shown at the game tables.
- Near a table the prompt **PLAY [E]** appears. Near the store: **SHOP [E]**.

## 3. Playing a table (free play)

- Pressing E picks the bots at random: 3 of the 5 for UNO, 1 of the 5 for checkers and for Connect Four.
- The player and the chosen bots walk to the table. When everyone has arrived the view zooms in and the game starts.
- At the table the player sees the opponents sitting across it.
- When the game ends a box appears:
  - win: "Congratulations!! You won!" and **+5 coins**;
  - loss: one of 20 sentences, picked at random;
  - tie (Connect Four only): a tie message and no coins.
- Enter closes the box and returns to the room.

### UNO
- 108 cards, 7 each, the first card on the table is a number.
- A card can be played if it matches the colour in play or the symbol, or if it is a wild.
- Skip, reverse, +2, wild and wild +4 work as in the official rules. +2 and +4 cannot be stacked.
- A player who cannot (or does not want to) play draws one card. If that card can be played, they may play it or pass.
- The first player with no cards wins.

### Checkers
- 8x8 board, the player is red and moves first.
- Men move one square diagonally forward. Kings move one square diagonally in any direction.
- Captures are mandatory, and a piece that can keep jumping must keep jumping.
- A man reaching the far row becomes a king.
- A side with no pieces or no legal move loses. After 60 moves without a capture, the side with more pieces wins (equal is a draw).

### Connect Four
- 7 columns, 6 rows. The player is red and moves first.
- Four in a row (across, up, or diagonal) wins. A full board with no winner is a tie.

## 4. Store

- Three tabs: hair, shirt, name tag.
- Each tab sells 20 common items (20 coins), 5 rare items (100 coins) and 1 legendary item (500 coins).
- A purchase is rejected if the player does not have enough coins or already owns the item. A rejected purchase changes nothing.
- A whole tab fits on one screen. Each item is a tile showing the item on the player's own character (the name tag
  with the player's name), and its price, or **OWNED**, or **WEARING**. A price the player cannot pay is shown in red.
- Clicking a tile shows the player wearing it, large, from the front, the side and the back, before buying.
  **Buy** pays for it (greyed out, with how many coins are missing, when the player cannot pay). An owned item can be
  worn straight away with **Wear it now**.
- The designs are our own. Themes: football (haircuts, kits in classic club colours with a number on the back,
  scarf name tags), battle royale (camo, helmet with visor, tactical vest, storm), and Portugal (azulejo tiles, the
  flag colours, the Barcelos rooster, the Nazare check, the Ribatejo stocking cap, Santos Populares). No real clubs,
  brands or people.

## 5. Pause menu and wardrobe

- Esc opens a light-blue menu: **Resume**, **Customize character**, **Leave arcade**.
- The wardrobe has the same three tabs and shows only owned items, with the character shown large on the right.
- Clicking an item previews it. **E** equips it and the item gets a green pixel tick. **U** takes it off and the default look returns.
- **Leave arcade** returns to the title screen. Progress is kept.

## 6. Championship

- The cabinet is locked until the player has won each of the three games at least once. Near it, a locked cabinet shows "LOCKED (must master all games to unlock)".
- Once unlocked the prompt is **START CHAMPIONSHIP [E]**.
- The first time only, a light-blue bubble explains the rules, one sentence per press of Enter, ending with "Are you ready?" and **Yes** / **No**. No returns to the room.
- From the second time on, the prompt also offers **RULES [I]**.
- Three bots are picked at random. Round 1 is UNO with all four players. In rounds 2 (checkers) and 3 (Connect Four) the player is drawn against one bot and the other two bots play each other (their result is simulated).
- A win is worth 2 points, a tie 1 point each. The maximum is 6.
- After each round a scoreboard shows "Winner: NAME" (or "Winners"), each player's head and name, a horizontal bar that grows with their points, and the number.
- After round 3 the final board shows one of 20 champion sentences (or one of 20 losing sentences). The champion is whoever has the most points. Sharing first place counts.
- Winning pays **50 coins**. Enter returns the player to the middle of the room.

## 7. Saved progress

Saved per player name: coins, owned cosmetics, equipped cosmetics, wins per game, championships won, and whether the championship introduction has been seen. Progress survives leaving the arcade and restarting the app.
