# Arcade Masters: game design

What the game must do. Tests and reviews are checked against this document.
Numbers live in `arcade/config.py`.

## 0. The game screen

- Every screen sits inside one glowing frame. The title screen and the arcade room are only the game picture,
  with no buttons around it, like a real game. The other screens have their buttons as a strip at the bottom of the
  frame. The frame is as big as the window allows without scrolling (checked at 1280x720, 1366x768, 1920x1080).
- Every button also has a key. **FULL SCREEN (F)** (top right) shows only the game, like a normal game.
  **MUSIC (M)** (top left) turns the music on and off.
- Music: five original chiptune tunes, all our own (`arcade/music.py`): a driving anthem on the title screen, a light,
  bouncy tune in the arcade room (also the store, wardrobe and championship), and one for each game (a funky party
  tune for UNO, a calm one for checkers, a hopping one for Connect Four). Changing screen fades from one to the
  next; the rules and the pause menu keep the tune that was playing. The music starts with the first key or click.
- Everything can be done with the mouse or with the keyboard. Where there is something to choose on the picture,
  the arrow keys move a **yellow highlight** and Space or Enter chooses it, like a click:

  | Screen | Keyboard |
  |---|---|
  | Pause menu | Up / Down move the highlight, Enter chooses it. Esc resumes. |
  | Championship YES / NO | Left / Right move the highlight, Enter chooses it (or Y / N). |
  | How to play | Left / Right (or 1-4) change tab. Esc goes back. |
  | Choose your opponent | Left / Right move the highlight, Space picks or un-picks that bot (or its number). Enter plays, Esc goes back. |
  | UNO | Left / Right move along your hand, Space plays that card (or picks it when it has twins, like a click). Enter plays the picked cards, X cancels them. Choosing a wild's colour: Left / Right and Enter (or Space); X cancels. D, P and U as before. |
  | Checkers | The arrow keys move a cursor on the board (blue, because yellow already marks the pieces); Space or Enter acts like a click on that square. |
  | Connect Four | Left / Right choose a column; Space, Enter or Down drops the disc. 1-7 drop straight into that column. |
  | Store | Left / Right choose an item, Up / Down change tab. Enter buys it (or wears it, if it is owned). Esc goes back. |
  | Wardrobe | Left / Right choose an item, Up / Down change tab. E equips it, U takes it off, Esc goes back. |

  The title screen and the arcade room already work both ways (sections 1 and 2).
- Changing screen fades in from black, smoothly (the browser does the fade).

## 1. Title screen

- Animated smoothly: twinkling stars, the neon floor grid sliding towards you, the four bots dancing under
  spotlights, the name of the game in big letters.
- It starts like an arcade machine waiting for a player: the name of the game drops in and **PRESS ENTER** blinks.
  Enter, Space or a click starts. This only happens the first time; coming back from HOW TO PLAY shows the menu.
- Clicking a bot, or pressing 1 to 4 (not while typing), makes it jump, spin and say a short line in a speech bubble.
- The arcade's best player dances on a gold podium at the right, in their own skins, with a crown and
  **CHAMPION xN**: the player with the most championships (a tie goes to more games won, then to the name in
  alphabetical order). Nobody stands there until someone has won a championship, and it changes as people play.
- Menu choices make arcade sounds (a coin when you confirm, a blip when you move), and the chosen option has a
  spinning coin on each side.
- The menu is drawn in the picture, like a real game: **PLAY OFFLINE**, **PLAY ONLINE** or **HOW TO PLAY** (arrow
  keys or W S to choose, Enter to confirm, Esc to go back, or the mouse). Both PLAY choices ask **NEW PLAYER** or
  **I HAVE AN ACCOUNT** (or BACK). PLAY OFFLINE flies into the arcade; PLAY ONLINE goes to the online menu
  (section 8).
- Then a panel with the boxes to type in (titled **ENTER YOUR NAME** for a new player, like an arcade high score):
  name and PIN (dots instead of digits). Arrow keys or Tab move between the
  boxes and the CREATE / LOG IN and BACK buttons. A refusal is written in red in the panel and the PIN boxes empty.
- New player: a name and a PIN of 4 to 8 digits, typed twice. A name that is already taken is refused.
- I have an account: the name and its PIN. A name that has never played is refused, and so is a wrong PIN
  (5 wrong PINs lock the name for a minute). A PIN cannot be recovered.
- Names: 1 to 10 characters, letters, numbers, spaces, `-` and `_`. Stored in capitals. Anything else is rejected with a message.
- A name that has played before continues with its saved coins, cosmetics, wins and championship status.
- When the sign-in is accepted, the camera flies forward into the arcade (about one second) and fades to black, and
  the arcade room fades in: the player enters the game without a cut.

## 2. Arcade room

- Pixel-art room seen from above. The player appears at the bottom, by the door, wearing the default clothes, with the name in a tag above the head.
- The player walks with W A S D (or arrow keys, or by clicking) and has four looks: down, up, left, right.
- Four bots, one per level, each with its own name and look (all our own designs): **DEAN** (easy, a university
  dean in a suit and glasses), **BARK** (medium, a dog with a blue bandana, on four legs), **MANHOSA** (hard, a
  security officer in uniform and cap) and **JOHN** (expert, the most ordinary guy there is).
- Three game tables stand out from the scenery: UNO (left), checkers (top middle), Connect Four (right).
- The store is at the top right. The championship cabinet is at the top left.
- A coin counter is shown at the top right of the room. It is not shown at the game tables.
- Near a table the prompt **PLAY [E]** appears. Near the store: **SHOP [E]**. Clicking a prompt does the same.
- No buttons under the room. A small pause button in the bottom-left corner opens the pause menu (like Esc).
- Starting a game: everyone walks to the table, the view zooms in and fades to black, and the table fades in.

## 3. Playing a table (free play)

- Pressing E opens **CHOOSE YOUR OPPONENT**: the four bots, from the easiest on the left to the hardest on the
  right, with their level, its stars and its coins.
  Checkers and Connect Four: pick 1. UNO: pick 3 (each plays at its own level). Click a card or press 1-4;
  clicking a picked bot takes it back. **PLAY** (Enter) starts once enough bots are picked; Esc goes back.
- Levels: **easy** (anyone who thinks a little wins), **medium** (a bit of strategy is enough), **hard** (you must
  know what you are doing), **expert** (only the best win). Settings per level in `config.py`. An easy Connect Four
  bot sometimes misses a four it could make or one it should stop; hard and expert never do.
  Simulated games (a **beginner** who plays almost at random, and a **fair** casual player), against easy / medium /
  hard / expert:

  | Game | Beginner wins | Fair player wins |
  |---|---|---|
  | Connect Four | 76 / 20 / 0 / 0 % | 100 / 88 / 15 / 3 % |
  | Checkers | 59 / 18 / 1 / – % | 96 / 85 / 9 / – % (expert is slow to simulate; it is stronger than hard) |
  | UNO (1st place out of 4) | 70 / 45 / 20 / 15 % | 81 / 64 / 34 / 27 % |
- The player and the chosen bots walk to the table. When everyone has arrived the view zooms in and the game starts.
- At the table the player sees the opponents sitting across it.
- A bot thinks for a random 1 to 3 seconds before each move, with a "..." speech bubble next to it (in checkers, the
  extra jumps of a chain follow quickly).
- The player has **15 seconds** for each turn, shown by a countdown bar under the table (red for the last 5 seconds).
  When time runs out the game plays for the player: in UNO they draw (or take the +2 / +4 cards) and their turn
  passes; in checkers and Connect Four a random legal move is played (every jump of a chain). Drawing a card in UNO
  or jumping again in checkers starts a fresh 15 seconds. Pausing or opening the rules stops the clock; it starts
  again from 15 on return.
- When the game ends a box appears:
  - win: "Congratulations!! You won!" and the coins of the bot's level: **easy 5, medium 15, hard 25, expert 40**;
  - UNO is played until only one player is left, so it has places. The prize is the average of the three bots'
    coins, rounded (easy + medium + hard = 15): **1st** wins all of it, **2nd** half, **3rd** a quarter (halves round
    up: 15 / 8 / 4), **last** nothing. The box shows everyone's place. Only 1st counts as a win (for the championship
    cabinet). Once the player has finished, the bots finish the game at once instead of the player watching;
  - loss: one of 20 sentences, picked at random;
  - tie (Connect Four only): a tie message and no coins.
- Enter closes the box and returns to the room.
- **Play again** (A, or a click on PLAY AGAIN in the box) starts the same game straight away, at the same table,
  against the same bots, for the same prize. It is only offered in free play: a championship goes on to its scoreboard.

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
- House rule, going out: nobody goes out with several cards at once. When a play would use the player's whole hand
  (for example their last two 1s), all but the last card go down and the player must say UNO; the last card then
  goes down by itself and they win. Missing UNO means drawing 2 and keeping that card.
- House rule, places: the first player with no cards finishes 1st and the others play on without them (they are
  skipped), until only one player has cards left: that player comes last. With two players left, a Reverse works
  like a Skip. A player who goes out by saying UNO on a turn that came back round to them passes the turn on.

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

- Esc opens a light-blue menu: **Resume**, **Wardrobe**, **How to play**, **Leave arcade**, and **Play online** in the
  room (O) or **Leave table** at a table.
- The wardrobe has the same three tabs and shows only owned items, with the character shown large on the right.
- Clicking an item previews it. **E** equips it and the item gets a green pixel tick. **U** takes it off and the default look returns.
- **Leave arcade** returns to the title screen. Progress is kept.

## 6. Championship

- The cabinet is locked until the player has won each of the three games at least once. Near it, a locked cabinet shows "LOCKED (must master all games to unlock)".
- Once unlocked the prompt is **START CHAMPIONSHIP [E]**.
- The first time only, a light-blue bubble explains the rules, one sentence per press of Enter, ending with "Are you ready?" and **Yes** / **No**. No returns to the room.
- From the second time on, the prompt also offers **RULES [I]**.
- Three bots are picked at random. Round 1 is UNO with all four players, played until only one player is left (like
  free play: once the player is out, the bots finish it at once). In rounds 2 (checkers) and 3 (Connect Four) the
  player is drawn against one bot and the other two bots play each other (their result is simulated).
- UNO round: 1st place gets 2 points, 2nd 1 point, 3rd and 4th nothing. Checkers and Connect Four: a win is worth
  2 points, a tie 1 point each. The maximum is 6.
- After each round a scoreboard shows "Winner: NAME" (or "Winners"; after UNO "1st: NAME (+2)" and the 2nd), each player's head and name, a horizontal bar that grows with their points, and the number.
- After round 3 the final board shows one of 20 champion sentences (or one of 20 losing sentences). The champion is whoever has the most points. Sharing first place counts.
- Winning pays **50 coins**. Enter returns the player to the middle of the room.

## 7. Saved progress

Saved per player name: coins, owned cosmetics, equipped cosmetics, wins per game, championships won, and whether the championship introduction has been seen. Progress survives leaving the arcade and restarting the app.

## 8. Playing online with friends

- Everyone plays on their own phone or laptop, at the game's web address. No bots online: only the people in the lobby.
- **Online menu**: **Create lobby** (N) gives a 4-letter code (no I or O, which look like 1 and 0). Friends type it in
  the box and press **Join** (or Enter). **Arcade** (A) goes back to playing offline; **Log out** (Esc) to the title.
- **Lobby**: up to **4 players**, shown with their own skins and name tags. The code is shown big, and as text with a
  copy button to paste into a message. Whoever created the lobby is the **host** (a crown): they pick the game, **UNO**
  (2 to 4 players), **Checkers** or **Connect Four** (exactly 2), and press **Start** when the number of players fits.
  The others see the host's choice and wait. Nobody can join while a game is being played.
- **At the table** each player sees the game from their own seat, with the same pictures as in the arcade: in UNO the
  others sit across the table in turn order; in checkers and Connect Four the host is red and moves first, and the
  second player's checkers board is turned round so their pieces are at the bottom. The same rules as offline (UNO
  places included). Moves out of turn are refused; a yellow frame shows whose turn it is.
- Each player has **15 seconds** a turn (shown under the table for everyone). When time runs out the game plays for them,
  as offline. In UNO, a player down to one card has 3 seconds to say UNO (U) or draws 2.
- Each browser looks for changes about once a second, so a friend's move shows up within about a second.
- Prizes: winning pays **15 coins** (like a medium bot); in UNO 1st / 2nd / 3rd get 15 / 8 / 4. Online wins do not count
  towards opening the championship cabinet (that is about beating the arcade's bots).
- **Lobby** (Enter) after a game goes back to the lobby, where the host can start another game. **Leave** (Esc) leaves:
  a game in progress then ends for everyone with no winner, and the next player becomes the host. The last player to
  leave closes the lobby.
