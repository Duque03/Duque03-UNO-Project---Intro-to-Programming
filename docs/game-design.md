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
- A bot thinks for a random 1 to 3 seconds before each move (in checkers, the extra jumps of a chain follow quickly).
- The player has **15 seconds** for each turn, shown by a countdown bar under the table (red for the last 5 seconds).
  When time runs out the game plays for the player: in UNO they draw (or take the +2 / +4 cards) and their turn
  passes; in checkers and Connect Four a random legal move is played (every jump of a chain). Drawing a card in UNO
  or jumping again in checkers starts a fresh 15 seconds. Pausing or opening the rules stops the clock; it starts
  again from 15 on return.
- UNO bots do not play perfectly: they play all their matching cards at once only sometimes, answer a +2 / +4 with
  their own only half the time, sometimes play a weaker card, and forget to say UNO a quarter of the time.
  (Settings in `config.py`. In 400 simulated games a careful player wins about half the time against them.)
- When the game ends a box appears:
  - win: "Congratulations!! You won!" and **+5 coins**;
  - loss: one of 20 sentences, picked at random;
  - tie (Connect Four only): a tie message and no coins.
- Enter closes the box and returns to the room.

### UNO
- 108 cards, 7 each, the first card on the table is a number.
- A play starts with a card that matches the colour in play or the symbol, or with a wild.
- House rule, several cards at once: with that first card you may play any other cards with the same number or
  symbol, in any order. The last card sets the colour (on a red pile: red 4, green 4, yellow 4 -> next is yellow).
  Several wilds share one chosen colour.
- Effects add up: each Skip skips one more player (3 skips with 4 players and you play again), each Reverse flips
  the order (two cancel out; with 2 players a Reverse works like a Skip), each +2 adds 2 and each +4 adds 4 cards.
- House rule, stacking: facing +2 you may answer with +2 cards, facing +4 with +4 cards; the total grows. A player
  who does not answer draws the total and loses the turn.
- House rule, drawing: a player who cannot (or does not want to) play keeps drawing until a card can be played,
  then may play it (with its twins) or pass.
- House rule, UNO: when a play leaves a player with one card they must say UNO within 2 seconds (button or U), or
  draw 2. Bots forget now and then.
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
- Each tab sells 10 common items (20 coins), 3 rare items (100 coins) and 1 legendary item (500 coins).
- A purchase is rejected if the player does not have enough coins or already owns the item. A rejected purchase changes nothing.
- A whole tab fits on one screen. Each item is a tile showing the item on the player's own character (the name tag
  with the player's name), and its price, or **OWNED**, or **WEARING**. A price the player cannot pay is shown in red.
- Clicking a tile shows the player wearing it, large, from the front, the side and the back, before buying.
  **Buy** pays for it (greyed out, with how many coins are missing, when the player cannot pay). An owned item can be
  worn straight away with **Wear it now**.
- The designs are our own. Themes: football (haircuts, kits in classic club colours with a number on the back,
  scarf name tags, the pitch), battle royale (camo, helmet with visor, tactical vest, storm), and Portugal (azulejo
  tiles, the flag colours, the Nazare check, the Ribatejo stocking cap, Santos Populares). Each tab has one rare item
  per theme. No real clubs, brands or people.

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
