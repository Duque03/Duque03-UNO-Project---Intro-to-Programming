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
  tune for UNO, a calm one for checkers, a hopping one for Connect Four). Changing screen fades quickly from one to
  the next, as soon as the new screen starts (a table's tune comes in with the table, not after the deal). The rules
  keep the tune that was playing; the **pause menu is quiet**. Each tune keeps its own time: after the pause menu,
  another screen, or the music switched off and on (M), it comes back where it would be had it kept playing unheard,
  not from the start. The pause menu also sets the **music level** (MUSIC: HIGH / MEDIUM / LOW, never off: that is
  M), kept with the player's progress. The music starts with the first key or click.
- Everything can be done with the mouse or with the keyboard. Where there is something to choose on the picture,
  the arrow keys move a **yellow highlight** and Space or Enter chooses it, like a click:

  | Screen | Keyboard |
  |---|---|
  | Pause menu | Up / Down move the highlight, Enter chooses it. Esc resumes. |
  | Championship YES / NO | Left / Right move the highlight, Enter chooses it (or Y / N). |
  | How to play | Left / Right (or 1-4) change tab. Esc goes back. |
  | Choose your opponent | Left / Right move the highlight, Space picks or un-picks that bot (or its number). Enter plays, Esc goes back. |
  | UNO | Left / Right move along your hand (the frame starts on the first card), Space picks or drops that card, like a click. Enter plays the picked cards, like a click on the discard pile; X cancels them. Choosing a wild's colour: Left / Right and Enter (or Space); X cancels. D draws, P passes; Space presses the big UNO! or CORTA UNO! button while it is up (online, Enter then plays the card the frame is on); in the face-off Y / N (or Left / Right and Enter). The yellow frame only shows while the keys are being used: a mouse click hides it, so nothing glows when playing with the mouse. |
  | Checkers | The arrow keys move a cursor on the board (blue, because yellow already marks the pieces); Space or Enter acts like a click on that square. |
  | Connect Four | Left / Right choose a column; Space, Enter or Down drops the disc. 1-7 drop straight into that column. |
  | Store | Left / Right choose an item, Up / Down change tab. Enter buys it (or wears it, if it is owned). Esc goes back. |
  | Wardrobe | Left / Right choose an item, Up / Down change tab. E or Enter equips it, U takes it off, Esc goes back. |

  The title screen and the arcade room already work both ways (sections 1 and 2).
- Going into a game and out of it (the three games, offline and online, and the championship's scoreboard), a
  purple **ARCADE MASTERS** screen comes down over the old screen (about 0.25 s), the new screen is made behind it,
  and it lifts (about 0.35 s) once the new screen has really drawn, after at least about 0.75 s: like a loading
  screen, so nothing in between is ever seen. Going into the arcade from the title (the flight) goes through black.
  The opponent picker is drawn over the room itself, which keeps moving behind it. Menus
  that open over the room or a table (the pause menu, the store, How to play) and the screens of
  the title menu are a plain cut: the previous picture stays until the new one is there, never a black flash. The
  screens opened from the title menu (making your character, the online menu, joining a lobby, How to play) are
  drawn on the title screen's own background, so only their box comes up. The online menu and the join box are drawn
  by the title screen itself: moving between them never changes the page at all.
- Never two screens at once: the old screen leaves the page as soon as the new one is there (no doubled picture, no
  small old picture in a corner), and a new picture fills the frame from its very first frame.
- No keyboard hints on the screen (no yellow key badges, no "ARROWS: CHOOSE"): the arrows and Enter move everywhere,
  E acts in the rooms, Space presses the big UNO! button. How to play lists every key. The one exception is the
  keys on the room's bubbles, which Miguel wants kept: **E** (PLAY, SHOP, TALK, START CHAMPIONSHIP, LEAVE SEAT) and
  **I** (RULES).

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
- The menu is drawn in the picture, like a real game (arrow keys or W S to choose, Enter to confirm, Esc to go back,
  or the mouse). First who you are: **CREATE A CHARACTER**, **I HAVE AN ACCOUNT** or **HOW TO PLAY**. Only after
  signing in (and, for a new player, making the character) comes where to play: "HELLO, ANA!" and **PLAY OFFLINE**,
  **PLAY ONLINE**, **HOW TO PLAY** or **LOG OUT**. PLAY OFFLINE flies into the arcade; PLAY ONLINE goes to the online
  menu (section 8). Leaving the arcade from the pause menu comes back to this choice.
- Then a panel with the boxes to type in (titled **ENTER YOUR NAME** for a new player, like an arcade high score):
  name and PIN (dots instead of digits). Arrow keys or Tab move between the
  boxes and the CREATE / LOG IN and BACK buttons. A refusal is written in red in the panel and the PIN boxes empty.
- New player: a name and a PIN of 4 to 8 digits, typed twice. A name that is already taken is refused.
- I have an account: the name and its PIN. A name that has never played is refused, and so is a wrong PIN
  (5 wrong PINs lock the name for a minute). A PIN cannot be recovered.
- Names: 1 to 10 characters, letters, numbers, spaces, `-` and `_`. Stored in capitals. Anything else is rejected with a message.
- A name that has played before continues with its saved coins, cosmetics, wins and championship status.
- After PLAY OFFLINE the camera flies forward into the arcade (about one second) and fades to black, and the arcade
  room fades in: the player enters the game without a cut.
- **Create your player** (only once, straight after the name and PINs of CREATE A CHARACTER, before choosing offline
  or online): the character
  stands on the left, the choices on the right: **hair** (boy or girl), **hair colour** (black, ginger, brown,
  blond), **T-shirt** (9 plain colours, nothing printed) and **skin** (6 tones). A click picks; Up / Down move between
  the rows and Left / Right change the choice (the yellow arrow only shows while the keys are used). **LET'S PLAY!**
  (or Enter) saves it. This is the player's base look: store hair and shirts go on top of it, and taking them off
  brings it back. Only the listed choices can be saved. Players who existed before this screen keep their look
  (short brown hair, white T-shirt).

## 2. Arcade room

- Pixel-art room seen from above. The player appears at the bottom, by the door, wearing their look, with the name in a tag above the head.
- The player walks with W A S D (or arrow keys, or by clicking) and has four looks: down, up, left, right. A click
  walks the player there round the tables and walls (the shortest way over the floor), not in a straight line that
  stops at the first table; a key, or a bot in the way, stops the walk.
- Four bots, one per level, each with its own name and look (all our own designs): **DEAN** (easy, a university
  dean in a suit and glasses), **BARK** (medium, a dog with a blue bandana, on four legs), **MANHOSA** (hard, a
  security officer in uniform and cap) and **JOHN** (expert, the most ordinary guy there is).
- The bots are alive: they stroll round the room (round the tables, never through them), stop to look at a machine,
  the store, the prize machine or the dance pad, look around, and move on. Now and then two of them sit down at a
  table nobody is using and play together for a while (never at the table the player stands at). When the player
  picks them for a game, they stop what they are doing and walk to the table; anyone else sitting there leaves.
- **Talking**: next to a bot, the prompt **TALK [E]** appears (but at a table, the store or the cup, PLAY / SHOP / START stay: E does that even with a bot there). E (or a click on it)
  makes the player say something and the bot answer, in speech bubbles above their heads, one after the other: thirty
  little exchanges per bot, in its own voice, all thirty before any repeats. DEAN is a formal, kind dean who loses a
  lot; MANHOSA a sly, strict security officer; JOHN painfully ordinary (and the best player there); BARK is a dog and
  only ever answers "Bark!". A bot stops and turns to the player while they talk (a bot playing at a table answers
  without getting up).
- Three game tables stand out from the scenery: UNO (left), checkers (top middle), Connect Four (right).
- The store is at the top right. The championship cabinet is at the top left.
- A coin counter is shown at the top right of the room. It is not shown at the game tables.
- Near a table the prompt **PLAY [E]** appears. Near the store: **SHOP [E]**. Clicking a prompt does the same.
- No buttons under the room. A small pause button in the bottom-left corner opens the pause menu (like Esc).
- Starting a game: everyone walks to the table, the view zooms in and fades to black, and the table fades in.

## 3. Playing a table (free play)

- Pressing E opens **CHOOSE YOUR OPPONENT** over the room (the room keeps moving, dimmed, behind it): the four
  bots, from the easiest on the left to the hardest on the right, with their level, its stars and its coins.
  Checkers and Connect Four: pick 1. UNO: pick 3 (each plays at its own level). Left / Right move the yellow frame,
  Space (or Enter) picks, 1-4 or a click picks that bot; picking it again takes it back. **PLAY** (Enter) starts
  once enough bots are picked; **BACK** (Esc) closes it.
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
- At the table the view is from the player's chair, in the same arcade as the room: behind each table is the part of
  the room's back wall that table faces (UNO: the championship cabinet and the gumball machine; checkers: the row of
  machines under the ARCADE sign and the store; Connect Four: the store and the prize machine), with the same bricks,
  bunting, neon strip, posters and confetti floor. The machines keep playing their little games, their lights chase,
  the claw moves, the neon signs flicker and the bunting changes colour (also in the room). The table is round, for
  four, and shows whole, sized for the players and the deck; the player's own hands hold their cards at the bottom. The opponents sit round it in turn
  order: one opponent sits across; two sit left and right; three sit left, across and right. The ones at the sides
  sit closer, so they look bigger. A lamp over the table lights the middle of the felt in flat pixel rings. In UNO
  each one holds their cards up in a fan, with how many they hold on the table in front of them. The draw pile and
  the discard pile lie flat in the middle, a little bigger than a card in the hand. After a wild, the discard pile
  glows in the colour that was chosen.
- A bot thinks for a random 1 to 3 seconds before each move; now and then (not every turn) a little "?" or "?!"
  bubble pops up next to its head (in checkers, the extra jumps of a chain follow quickly).
- **Who starts is random in every game.** UNO shows it with the roulette after the deal (below); checkers and Connect
  Four start with a roulette that goes between the two score cards and stops on whoever starts ("YOU START!" /
  "DEAN STARTS!"); its yellow frame hugs the score cards, and "Your turn" only shows once it has stopped. The player's
  15 seconds only start after it. Messages beside the board (a random move after the
  time ran out, a refused move) wrap onto several lines under the player's score card, so they always fit.
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
- House rule, UNO: when a play leaves a player with one card, a big **UNO!** button (a comic-book burst of our own)
  appears in the middle of the table: a click or **Space** says it. It has **no time limit** and being slow costs
  nothing by itself: the button stays until the player presses it, or until someone cuts the UNO first (Corta UNO,
  below). Offline the game waits for it. Bots always say their UNO.
- Facing a +2 / +4 with nothing to answer it, the player takes the cards straight away (they fly to the hand): there
  is nothing to choose. With a card that can answer it, they choose as usual.
- Whose turn it is: that player lights up a little and their name glows (no frame around them).
- House rule, **Corta UNO**: while a player who is down to one card has not said UNO yet, anyone else can press
  the big **CORTA UNO!** button in the middle of the table (a click or Space). If they are first, the two of them play a **trivia face-off**:
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
  goes down by itself and they win. A cut UNO means drawing 7 and keeping that card.
- House rule, places: the first player with no cards finishes 1st and the others play on without them (they are
  skipped), until only one player has cards left: that player comes last. A player who has finished but is still at
  the table (online, while the others play on) sees their own place where their cards were: a medal and
  **1ST PLACE!** (2ND, 3RD...). With two players left, a Reverse works
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

- Esc opens a light-blue menu: **Resume**, **Wardrobe**, **How to play**, **Music: High** (each click or Enter goes
  to Medium, Low, High again), **Leave arcade**, and **Play online** in the room or **Leave table** at a table.
  **Play online** opens the online menu (section 8). In the online lobby the last choice is **Leave lobby**, which goes
  back to the choice of offline or online.
  The music stops while the menu is open, and stays off in everything opened from it (wardrobe, how to play).
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
- **Online menu**: a box over the title screen, whose animation keeps going behind it (stars, floor grid, arcade
  machines). Your character dances inside the box with their moving name tag, beside four big white buttons; the
  chosen one turns yellow with a spinning coin on each side. Up / Down move, Enter or a click chooses:
  **CREATE LOBBY** gives a 4-letter code and walks you into the lobby; **JOIN A LOBBY**; **PLAY OFFLINE** flies into
  the arcade; **GO BACK** (or Esc) returns to the choice of offline or online ("HELLO, ANA!"), never to the name.
  Pressing CREATE LOBBY several times quickly makes one lobby (the button says "..." until the lobby is there).
- **Join a lobby**: four boxes for the code, like an arcade's high-score letters. Type the letters on the keyboard, or
  move along an on-screen keyboard with the arrows and press Enter (or click / tap a letter: phones have no keyboard).
  Backspace or DEL deletes; once the 4th letter is in, the highlight jumps to JOIN and Enter joins; Esc or BACK goes
  back to the online menu. Codes never use I or O (they look like 1 and 0), C or R (Streamlit keeps those keys) or M and F (music and
  full screen), so every letter of a code can be typed.
- **The lobby is a room like the arcade** (like Club Penguin): up to **4 players**, each with their own look and name
  tag, walking about with the same keys and clicks as offline. No bots: the people in the lobby are the ones walking
  about (they come in by the door). The lobby's code and how many are in is on a plate at the bottom right, to give to
  friends. Someone can join while others are playing at a table. The **store** works as offline (SHOP at the counter;
  the others see you standing there; back to the room after). The championship is offline only for now (its cabinet
  says COMING SOON...). "Welcome back" pops up once you are in the room, not on the online menu.
- **Chat**: a bar at the bottom of the picture. **Enter** (or a click / tap on the box) to type (the box lights up
  and a **|** blinks where the next letter goes), **Enter** to send, **Esc** to give up. What is said shows in a
  speech bubble above the player's head for 6 seconds (your own light blue, the others' cream). Messages are short
  (40 letters) and written as typed, in the game's pixel font: small and capital letters and Portuguese accents
  (ã, õ, ê, ç, á...). Rude words, in English and Portuguese, turn into stars. Not too fast: a message every 1.2 seconds and at most 5
  in 10 seconds ("Slow down a little!").
- **Emojis**: the face on the left of the bar (or **Tab**) opens a panel of 12 pixel emojis of our own (smile, laugh,
  wink, cool, love, wow, sad, angry, heart, thumbs up, trophy, GG). Click one, or move the yellow frame with the arrows
  and press Enter; Esc or Tab closes it. The emoji pops up above the player's head like a message.
- **Tables**: each table has a sign over it with a square per chair and the count (**1/4**, **2/4**...), and a mat on
  the floor at every chair, lit where someone sits. Walk to a table and press **E** (or click PLAY): your character
  sits on a free chair and stays there, waiting. **E** again (LEAVE SEAT) or walking away gets up. **Checkers** and **Connect Four** start as
  soon as both chairs are taken. **UNO** starts at **4/4**, or **10 seconds** after the second player sat down (the
  sign counts down: STARTS IN 7); with 2 or 3 it starts with those seated. A table that is playing shows PLAYING and
  takes nobody else; the other tables are free, so two games can be played at the same time. Esc in the room opens the
  pause menu (RESUME, WARDROBE, HOW TO PLAY, MUSIC, LEAVE LOBBY) and gets up from any chair first, so a game never
  starts with someone reading a menu. Clothes changed in the wardrobe are seen by the others.
- **At the table** each player sees the game from their own seat, with the same pictures as in the arcade: in UNO the
  others sit round the table in turn order; in checkers and Connect Four the second player's checkers board is turned round so their pieces are at the bottom. The same rules as offline (UNO
  places included). Moves out of turn are refused; a yellow frame shows whose turn it is. In checkers and Connect Four
  the first chair is red and moves first (a roulette shows who starts).
- Each player has **15 seconds** a turn (shown at the top for everyone). When time runs out the game plays for them,
  as offline. In UNO, a player down to one card says UNO with the big button (a click or Space), with no time limit; until
  then any other player at the table can cut it (the big CORTA UNO! button). Online games also start with
  the roulette (the server picks who starts; UNO after the deal), so the first turn gets 9 more seconds in UNO and 4
  in checkers and Connect Four; each browser animates the cards that moved since it last looked.
- Each browser looks for changes about once a second, so a friend's move shows up within about a second.
- Prizes: winning pays **15 coins** (like a medium bot); in UNO 1st / 2nd / 3rd get 15 / 8 / 4. Online wins do not count
  towards opening the championship cabinet (that is about beating the arcade's bots).
- **Lobby** (Enter) after a game goes back to the room, standing by the table; the table is free again once everyone
  who played has gone back. **Leave** (Esc, or X in the corner) in the middle of a game goes back to the room too: the
  game then ends for the others with no winner. **LEAVE LOBBY** in the pause menu leaves the lobby (a game the player
  is in ends the same way). The last player to leave closes the lobby.
