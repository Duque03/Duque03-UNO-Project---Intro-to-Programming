# Arcade Masters: game design

What the game must do. Tests and reviews are checked against this document.
Numbers live in `arcade/config.py`.

## 0. The game screen

- The game is always just the game picture, filling the window (16:9, as big as the window allows, in the middle,
  without scrolling; checked at 1366x768, 1920x1080 and a taller 1000x900). There is no frame, no header and no row of
  buttons: every button is drawn on the picture and also has a key. The countdown of a turn sits on the picture, at
  the top in the middle.
- Two small icons in the top-left corner: the note turns the music on and off (M), the arrow shows only the game,
  like a normal game (F, full screen).
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
  | UNO | Left / Right move along your hand (the frame starts on the first card), Space picks or drops that card, like a click. Enter plays the picked cards, like a click on the discard pile; X cancels them. Choosing a wild's colour: Left / Right and Enter (or Space); X cancels. D draws, P passes, U says UNO, K cuts a UNO; in the face-off Y / N (or Left / Right and Enter). The yellow frame only shows while the keys are being used: a mouse click hides it, so nothing glows when playing with the mouse. |
  | Checkers | The arrow keys move a cursor on the board (blue, because yellow already marks the pieces); Space or Enter acts like a click on that square. |
  | Connect Four | Left / Right choose a column; Space, Enter or Down drops the disc. 1-7 drop straight into that column. |
  | Store | Left / Right choose an item, Up / Down change tab. Enter buys it (or wears it, if it is owned). Esc goes back. |
  | Wardrobe | Left / Right choose an item, Up / Down change tab. E or Enter equips it, U takes it off, Esc goes back. |

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
- **Create your player** (only once, right after NEW PLAYER, before the arcade or the online menu): the character
  stands on the left, the choices on the right: **hair** (boy or girl), **hair colour** (black, ginger, brown,
  blond), **T-shirt** (9 plain colours, nothing printed) and **skin** (6 tones). A click picks; Up / Down move between
  the rows and Left / Right change the choice (the yellow arrow only shows while the keys are used). **LET'S PLAY!**
  (or Enter) saves it. This is the player's base look: store hair and shirts go on top of it, and taking them off
  brings it back. Only the listed choices can be saved. Players who existed before this screen keep their look
  (short brown hair, white T-shirt).

## 2. Arcade room

- Pixel-art room seen from above. The player appears at the bottom, by the door, wearing their look, with the name in a tag above the head.
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
- At the table the view is from the player's chair, close to a round table for four that shows whole, sized for the
  players and the deck; the player's own hands hold their cards at the bottom. The opponents sit round it in turn
  order: one opponent sits across; two sit left and right; three sit left, across and right. The ones at the sides
  sit closer, so they look bigger. A lamp over the table lights the middle of the felt in flat pixel rings. In UNO
  each one holds their cards up in a fan, with how many they hold on the table in front of them. The draw pile and
  the discard pile lie flat in the middle, a little bigger than a card in the hand. After a wild, the discard pile
  glows in the colour that was chosen.
- A bot thinks for a random 1 to 3 seconds before each move, with a "..." speech bubble next to it (in checkers, the
  extra jumps of a chain follow quickly).
- The player has **15 seconds** for each turn, shown by a pixel countdown strip at the top (red for the last 5 seconds).
  When time runs out the game plays for the player: in UNO they draw (or take the +2 / +4 cards) and their turn
  passes; in checkers and Connect Four a random legal move is played (every jump of a chain). Drawing a card in UNO
  or jumping again in checkers starts a fresh 15 seconds. Pausing or opening the rules stops the clock; it starts
  again from 15 on return.
- When the game ends everyone stands on a **podium** (pixel art, also online): the winner on the gold step under a
  spotlight with a medal, the loser on the silver step beside it (a tie: both on two equal gold steps), the title on a
  red ribbon, the coins, and a line on the stage. They drop onto their steps one by one, the winner last; confetti
  when the player wins. What it says:
  - win: "Congratulations!! You won!" and the coins of the bot's level: **easy 5, medium 15, hard 25, expert 40**;
  - UNO is played until only one player is left, so it has places. The prize is the average of the three bots'
    coins, rounded (easy + medium + hard = 15): **1st** wins all of it, **2nd** half, **3rd** a quarter (halves round
    up: 15 / 8 / 4), **last** nothing. Instead of a box, everyone stands on a **podium** (also online): 1st in the
    middle and highest, 2nd on the left, 3rd on the right, each with a gold, silver or bronze medal, and the last
    player beside it on the floor. They drop onto their steps one by one, the last player first and the winner last,
    under a spotlight (confetti when the player wins), with the title, the coins, and CONTINUE / PLAY AGAIN (online:
    LOBBY). Only 1st counts as a win (for the championship cabinet). Once the player has finished, the bots finish the
    game at once instead of the player watching;
  - loss: one of 20 sentences, picked at random;
  - tie (Connect Four only): a tie message and no coins.
- Enter (or a click) closes the podium and returns to the room.
- **Play again** (A, or a click on PLAY AGAIN) starts the same game straight away, at the same table,
  against the same bots, for the same prize. It is only offered in free play: a championship goes on to its scoreboard.

### UNO
- 108 cards, 7 each, the first card on the table is a number. The deck is a real UNO deck (per colour: one 0, two of
  each 1 to 9, two Skip, two Reverse, two +2; plus 4 Wild and 4 Wild +4), shuffled at the start; when it runs out,
  the discard pile (all but its top card) is shuffled into a new deck. So every card comes up as often as in a real
  game; tests check the deck, how often each card is dealt over thousands of deals, and that no card is ever lost.
- No messages on the table: what happens is seen (cards fly, the countdown runs) and how to play is in the rules. Picked cards just stand up, with no numbers on them.
- There is no row of buttons under the picture: everything is on it. The deck draws, the pile plays, a picked card
  clicked again goes back down, **PASS** appears beside the deck after drawing, and **RULES** and **PAUSE** sit in
  the top-right corner (online: **LEAVE**). The keys still work (D, Enter, X, P, U, K, H, Esc).
- The start of a game is shown: the cards are dealt one at a time from the deck, around the table starting with the
  player (the player's own cards land face up, in order), the first card of the pile turns up, then a **roulette**
  lights the players one after the other, slows down and stops on the one who starts ("BARK STARTS!" / "YOU
  START!"). Who starts is random. The player's 15 seconds only start after the roulette.
- Cards move: a card drawn flies from the deck to the hand, cards played fly to the pile one at a time, for the
  player and for every opponent (online too, for everyone at the table). Python waits for each animation to end
  before the next move, so nothing changes on the table meanwhile.
- A play starts with a card that matches the colour in play or the symbol, or with a wild.
- House rule, several cards at once: with that first card you may play any other cards with the same number or
  symbol, in any order. The last card sets the colour (on a red pile: red 4, green 4, yellow 4 -> next is yellow).
  Several wilds share one chosen colour.
- Effects add up: each Skip skips one more player (3 skips with 4 players and you play again), each Reverse flips
  the order (two cancel out; with 2 players a Reverse works like a Skip), each +2 adds 2 and each +4 adds 4 cards.
- House rule, stacking: facing +2 you may answer with +2 cards, facing +4 with +4 cards; the total grows. A player
  who does not answer draws the total and loses the turn.
- House rule, drawing: on their turn a player may draw whenever they like, one card at a time (D or a click on the
  deck), at most **2 cards** a turn. After a draw they may play any card that fits or pass (P). With nothing to play
  after the second card, the turn passes by itself.
- Playing: nothing in the hand glows (finding a card that fits is part of the game). A click on a card picks it (it
  stands up a little); cards with the same number or symbol can be picked with it; a click on a picked card drops it.
  A click on the **discard pile** (or Enter) plays the picked cards in the order they were picked; with nothing picked
  it does nothing. If the first picked card does not fit, a message says so and nothing is played.
- House rule, UNO: when a play leaves a player with one card they must say UNO within 2 seconds (button or U), or
  draw 2. Bots forget now and then.
- Facing a +2 / +4 with nothing to answer it, the player takes the cards straight away (they fly to the hand): there
  is nothing to choose. With a card that can answer it, they choose as usual.
- Whose turn it is: that player lights up a little and their name glows (no frame around them).
- House rule, **Corta UNO**: while a player who is down to one card has not said UNO yet, anyone else can press
  **CORTA UNO!** (K, or the button on the table). If they are first, the two of them play a **trivia face-off**:
  yes-or-no questions, **8 seconds** each (Y / N, Left / Right and Enter, or a click; no answer counts as wrong).
  When both are right or both are wrong, another question comes. As soon as one is right and the other is wrong it is
  over: if the player with UNO was wrong they draw **7 cards**; if the one who cut was wrong the UNO stands, as if it
  had been said (the waiting last card goes down). Nothing happens to the other player either way.
  - Bots cut the player's UNO too: each bot level has a chance to try and a reaction time, counted from when the
    UNO button shows (easy rarely and slowly, expert often and fast; even the fastest needs more than a second, so a
    player who says UNO straight away is never cut). A bot down to one card waits a moment before saying UNO (easy longer, expert shorter):
    that is when the player can cut it. Bots answer right more often the higher their level (easy 55%, medium 70%,
    hard 82%, expert 92%). Bots do not cut each other.
  - Online, any player at the table can cut another's UNO. The game waits during the face-off; the others watch it.
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
- The store is one picture in pixel art, like the rest of the game: a dark bar at the top with the title, the coins in
  a box, the tabs (folder tabs) and **BACK**. A whole tab fits on it: the items stand on wooden shelves on a pegboard
  wall, by rarity (a hanging sign for each). Each tile shows **only the item**: the hair on a plain head shape (no
  face), the shirt on a hanger, the name tag with the player's name. Along the bottom of the tile: the price, or
  **OWNED**, or **WEARING**; a price the player cannot pay is pink with a padlock. Rare and legendary tiles are a
  little wider, and the legendary one sparkles.
- Clicking a tile shows the player wearing it on the right, in a small fitting room with curtains: large, from the
  front, the side and the back, lit in the colour of the item's rarity, with its name, rarity and price. On the
  counter below, **BUY FOR ...** pays for it (dim, with a bar of how many coins the player has towards the price,
  when they cannot pay). An owned item can be worn straight away with **WEAR IT**.
- The designs are our own. Themes: football (haircuts, kits in classic club colours with a number on the back,
  scarf name tags, the pitch), battle royale (camo, helmet with visor, tactical vest, storm), and Portugal (azulejo
  tiles, the flag colours, the Nazare check, the Ribatejo stocking cap, Santos Populares). Each tab has one rare item
  per theme. No real clubs, brands or people.

## 5. Pause menu and wardrobe

- Esc opens a light-blue menu: **Resume**, **Wardrobe**, **How to play**, **Leave arcade**, and **Play online** in the
  room (O) or **Leave table** at a table.
- The wardrobe is a picture like the store, with only owned items, and the character in the fitting room on the right.
- Clicking an item previews it. **EQUIP** (E or Enter) wears it (its tile says WEARING). **UNEQUIP** (U) takes it off
  and the player's own look (made when they created their player) returns.
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
- **Online menu**, drawn on the picture like the pause menu (Up / Down move the yellow highlight, Enter or a click
  chooses): **CREATE LOBBY** (N) gives a 4-letter code; **JOIN A LOBBY** (J); **PLAY OFFLINE** (A) goes back into the
  arcade; **LOG OUT** (Esc) to the title.
- **Join a lobby**: four boxes for the code, like an arcade's high-score letters. Type the letters on the keyboard, or
  move along an on-screen keyboard with the arrows and press Enter (or click / tap a letter: phones have no keyboard).
  Backspace or DEL deletes, Enter or JOIN joins (the highlight jumps to JOIN after the 4th letter), Esc or BACK goes
  back. Codes never use I or O (they look like 1 and 0), C or R (Streamlit keeps those keys) or M and F (music and
  full screen), so every letter of a code can be typed.
- **Lobby**: up to **4 players**, shown with their own skins and name tags. The code is shown big, and as text with a
  copy button to paste into a message. Whoever created the lobby is the **host** (a crown): they pick the game on the
  picture (Left / Right, a click, or 1 / 2 / 3): **UNO** (2 to 4 players), **Checkers** or **Connect Four** (exactly 2),
  and press **Start** (Enter) when the number of players fits.
  The others see the host's choice and wait. Nobody can join while a game is being played.
- **At the table** each player sees the game from their own seat, with the same pictures as in the arcade: in UNO the
  others sit round the table in turn order; in checkers and Connect Four the host is red and moves first, and the
  second player's checkers board is turned round so their pieces are at the bottom. The same rules as offline (UNO
  places included). Moves out of turn are refused; a yellow frame shows whose turn it is.
- Each player has **15 seconds** a turn (shown at the top for everyone). When time runs out the game plays for them,
  as offline. In UNO, a player down to one card has 3 seconds to say UNO (U) or draws 2. Online UNO also starts with
  the deal and the roulette (the server picks who starts), so the first turn gets 9 more seconds; each browser
  animates the cards that moved since it last looked.
- Each browser looks for changes about once a second, so a friend's move shows up within about a second.
- Prizes: winning pays **15 coins** (like a medium bot); in UNO 1st / 2nd / 3rd get 15 / 8 / 4. Online wins do not count
  towards opening the championship cabinet (that is about beating the arcade's bots).
- **Lobby** (Enter) after a game goes back to the lobby, where the host can start another game. **Leave** (Esc) leaves:
  a game in progress then ends for everyone with no winner, and the next player becomes the host. The last player to
  leave closes the lobby.
