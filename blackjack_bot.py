from blackjack import BlackjackGame, Deck

class GameStats:
    """tracks statistics across multiple games"""
    
    def __init__(self):
        """initialize counters for wins, losses, pushes, and blackjacks"""
        self.wins = 0
        self.losses = 0
        self.pushes = 0
        self.blackjacks = 0
        self.busts = 0
        self.total_games = 0
        self.bankroll = 0
        self.total_bet = 0
    
    def record_result(self, result: str, bet_amount: int, is_blackjack: bool = False, is_bust: bool = False):
        """
        record the outcome of a single game
        result: 'win', 'loss', or 'push'
        is_blackjack: whether player got a natural blackjack
        is_bust: whether player busted
        """
        self.total_games += 1
        self.total_bet += bet_amount
        
        if result == 'win':
            self.wins += 1
            if is_blackjack:
                self.blackjacks += 1
                self.bankroll += bet_amount * 1.5  # blackjack pays out 3:2
            else:
                self.bankroll += bet_amount
        elif result == 'loss':
            self.losses += 1
            self.bankroll -= bet_amount
            if is_bust:
                self.busts += 1
        elif result == 'push':
            self.pushes += 1
    
    def get_win_rate(self) -> float:
        """calculate win percentage (excluding pushes)"""
        if self.wins + self.losses == 0:
            return 0.0
        return (self.wins / (self.wins + self.losses)) * 100
    
    def print_summary(self):
        """display a summary of all game results"""
        print("\n" + "=" * 50)
        print("GAME STATISTICS")
        print("=" * 50)
        print(f"Total games played: {self.total_games}")
        print(f"Wins: {self.wins} ({self.wins / self.total_games * 100:.1f}%)")
        print(f"Losses: {self.losses} ({self.losses / self.total_games * 100:.1f}%)")
        print(f"Pushes: {self.pushes} ({self.pushes / self.total_games * 100:.1f}%)")
        print(f"\nWin rate (excluding pushes): {self.get_win_rate():.2f}%")
        print(f"Blackjacks: {self.blackjacks}")
        print(f"Busts: {self.busts}")
        print(f"Profit (bankroll): {self.bankroll:.2f} units")
        if self.total_bet > 0:
            print(f"ROI: {self.bankroll / self.total_bet * 100:.2f}%")
        print("=" * 50)
    
    def to_dict(self):
        """return stats as a dictionary for easy export"""
        return {
            'total_games': self.total_games,
            'wins': self.wins,
            'losses': self.losses,
            'pushes': self.pushes,
            'win_rate': self.get_win_rate(),
            'blackjacks': self.blackjacks,
            'busts': self.busts,
            'win_pct': self.wins / self.total_games * 100 if self.total_games > 0 else 0,
            'loss_pct': self.losses / self.total_games * 100 if self.total_games > 0 else 0,
            'push_pct': self.pushes / self.total_games * 100 if self.total_games > 0 else 0,
            'bankroll': self.bankroll,
            'roi_pct': (self.bankroll / self.total_bet * 100) if self.total_bet > 0 else 0
        }


class BlackjackBot:
    """bot that can play multiple games and track results"""
    
    def __init__(self, strategy_func, silent: bool = False, use_card_counting: bool = False, num_decks: int = 1, shuffle_threshold: float = 75.0):
        """
        initialize bot with a strategy function
        strategy_func: function that takes game state and returns 'hit' or 'stand'
        silent: if True, suppress game output for faster batch processing
        use_card_counting: if True, maintains a card counter across games
        num_decks: number of decks in the shoe (1 for single deck, 6-8 for casino)
        shuffle_threshold: reshuffle when this % of cards dealt (70-80% is casino standard)
        """
        self.strategy = strategy_func
        self.stats = GameStats()
        self.silent = silent
        self.use_card_counting = use_card_counting
        self.counter = CardCounter() if use_card_counting else None
        self.current_game_result = None
        self.num_decks = num_decks
        self.shuffle_threshold = shuffle_threshold
        self.deck = None  # will be created when playing
    
    def get_bet_size(self, true_count):
        # bet ramp based on true count (higher count = bet MORE)
        # if count is below 0 (very bad) bet nothing and "pass" on that hand (you will get caught in a casino if you do this)
        if true_count < 0:
            return 0
        elif true_count < 1:
            return 1
        if true_count < 2:
            return 2
        elif true_count < 3:
            return 5
        elif true_count < 4:
            return 10
        elif true_count < 5:
            return 25
        else:
            return 50
    
    def play_games(self, num_games: int):
        """
        play multiple games and track statistics
        num_games: number of games to play
        """
        shoe_info = f"{self.num_decks}-deck shoe" if self.num_decks > 1 else "single deck"
        print(f"\nPlaying {num_games} games with {shoe_info}...")
        print(f"Reshuffling at {self.shuffle_threshold}% penetration")
        
        # create initial deck/shoe
        self.deck = Deck(num_decks=self.num_decks)
        
        # reset counter at start if using card counting
        if self.counter:
            self.counter.reset()
        
        for i in range(num_games):
            # check if we need to reshuffle
            if self.deck.needs_shuffle(self.shuffle_threshold):
                # create new shoe and reset counter
                self.deck = Deck(num_decks=self.num_decks)
                if self.counter:
                    self.counter.reset()
            
            # determine bet size
            if self.counter:
                cards_left = self.deck.cards_remaining()
                decks_remaining = max(cards_left / 52, 0.5)
                true_count = self.counter.get_true_count(decks_remaining)
                self.current_bet = self.get_bet_size(true_count)
            else:
                self.current_bet = 1

            # create new game with existing deck (casino style)
            game = BlackjackGame(deck=self.deck, counter=self.counter)
            self.current_game_result = None
            
            # temporarily suppress print if silent mode
            if self.silent:
                import sys
                import io
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
            
            try:
                # play the game
                game.play(get_action=self._bot_action_wrapper(game))

                # determine result after game completes
                self._record_game_result(game)
            finally:
                # restore stdout if it was suppressed
                if self.silent:
                    sys.stdout = old_stdout
        
        # display final statistics
        #self.stats.print_summary()
    
    def _bot_action_wrapper(self, game):
        """
        wrapper that returns a function for getting bot actions
        this allows us to track game state and results
        """
        def get_action(g):
            # if using card counting, pass counter to strategy
            if self.counter:
                return self.strategy(g, self.counter)
            return self.strategy(g)
        return get_action
    
    def _record_game_result(self, game):
        """
        analyze final game state and record the result
        determines if player won, lost, or pushed
        """
        player_val = game.player_hand.get_value()
        dealer_val = game.dealer_hand.get_value()
        player_bust = game.player_hand.is_bust()
        dealer_bust = game.dealer_hand.is_bust()
        player_bj = game.player_hand.is_blackjack()
        dealer_bj = game.dealer_hand.is_blackjack()

        bet = self.current_bet
        
        # determine result based on game state
        if player_bust:
            self.stats.record_result('loss', bet, is_bust=True)
        elif dealer_bust:
            self.stats.record_result('win', bet)
        elif player_bj and not dealer_bj:
            self.stats.record_result('win', bet, is_blackjack=True)
        elif dealer_bj and not player_bj:
            self.stats.record_result('loss', bet)
        elif player_val > dealer_val:
            self.stats.record_result('win', bet)
        elif player_val < dealer_val:
            self.stats.record_result('loss', bet)
        else:
            self.stats.record_result('push', bet)


def num_strategy(game, hit_num: int):
    """
    simple strategy: hit on specific number or less, stand on otherwise
    this mimics basic dealer strategy
    (ideal should be hit_num = 16)
    """
    if game.player_hand.get_value() <= hit_num:
        return 'hit'
    return 'stand'


def basic_strategy(game):
    """
    optimal basic strategy that mathematically maximizes expected value
    this is the standard "perfect play" for blackjack without card counting
    follows the standard basic strategy chart used in casinos
    """
    player_value = game.player_hand.get_value()
    dealer_up_card = game.dealer_hand.cards[0]
    
    # get dealer up card value
    if dealer_up_card.rank in ['J', 'Q', 'K']:
        dealer_value = 10
    elif dealer_up_card.rank == 'A':
        dealer_value = 11
    else:
        dealer_value = int(dealer_up_card.rank)
    
    # check for soft hand (hands with an ace counted as 11)
    has_ace = any(card.rank == 'A' for card in game.player_hand.cards)
    is_soft = False
    
    # verify if we have a soft hand (ace still counted as 11, not forced to 1)
    if has_ace:
        # calculate what value would be if all aces were 1
        hard_value = sum(10 if c.rank in ['J','Q','K'] else (1 if c.rank == 'A' else int(c.rank)) 
                        for c in game.player_hand.cards)
        # if current value differs from hard value, we have a soft hand
        is_soft = (player_value != hard_value) and player_value <= 21
    
    # soft hand strategy (ace counted as 11)
    if is_soft:
        if player_value >= 19: # soft 19-21
            return 'stand'
        elif player_value == 18: # soft 18
            # hit against strong dealer cards
            if dealer_value in [9, 10, 11]:
                return 'hit'
            return 'stand'
        else: # soft 17 or less
            return 'hit'
    
    # hard hand strategy (ace counted as 1)
    if player_value >= 17:
        return 'stand'
    elif player_value <= 11:
        return 'hit' # always safe to hit, cant bust
    elif player_value == 12:
        # stand against dealers weak cards (4-6)
        if dealer_value in [4, 5, 6]:
            return 'stand'
        return 'hit'
    elif player_value in [13, 14, 15, 16]:
        # stand when dealer shows 2-6 (likely to bust)
        if dealer_value in [2, 3, 4, 5, 6]:
            return 'stand'
        return 'hit'
    
    # default case
    return 'stand'


class CardCounter:
    """
    implements Hi-Lo card counting system
    high cards (10, J, Q, K, A) = -1 (BAD if we see a high card since it reduces the number of remainining high cards)
    neutral cards (7, 8, 9) = 0
    low cards (2, 3, 4, 5, 6) = +1 (GOOD if we see a low card since it means there are more high cards remaining)
    """
    
    def __init__(self):
        """initialize the running count and tracking structures"""
        self.running_count = 0
        self.cards_seen = 0
        self.seen_cards = set() # track which specific card objects weve counted
    
    def update(self, card):
        """
        update the count based on a card that was seen
        card: Card object that was just dealt
        
        IMPORTANT: uses object id to prevent double-counting the same card
        this is critical because we see some cards during play and count
        all cards again at the end of the hand
        """
        # use card object id to avoid double counting the same physical card
        card_id = id(card)
        if card_id in self.seen_cards:
            return # already counted this specific card object
        
        # mark this card as seen
        self.seen_cards.add(card_id)
        self.cards_seen += 1
        
        # hi-lo counting system values
        if card.rank in ['2', '3', '4', '5', '6']:
            # if we see a LOW card, it is GOOD for the player, since increases chances of a HIGH card later
            self.running_count += 1
        elif card.rank in ['10', 'J', 'Q', 'K', 'A']:
            # if we see a HIGH card, it is BAD for the player, since there are less HIGH cards left
            self.running_count -= 1
        # 7, 8, 9 are neutral (count = 0, no change)
    
    def get_true_count(self, decks_remaining: float = None) -> float:
        """
        calculate true count (running count divided by decks remaining)
        
        normalizes the running count based on how many decks are left
        ex: a running count of +6 means more in a single deck than in a 6 deck shoe
        
        decks_remaining: estimated decks left in shoe (if None, uses estimate)
        """
        if decks_remaining is None:
            # rough estimate: assume single deck if not specified
            cards_remaining = 52 - self.cards_seen
            decks_remaining = max(cards_remaining / 52, 0.5)
        
        # avoid division by zero
        if decks_remaining <= 0:
            decks_remaining = 0.5
        
        return self.running_count / decks_remaining
    
    def reset(self):
        """reset the count (called when deck is shuffled)"""
        self.running_count = 0
        self.cards_seen = 0
        self.seen_cards.clear()


def card_counting_strategy(game, counter: CardCounter):
    """
    uses basic strategy as foundation, but modifies based on the true count
    
    positive count = more high cards left in deck
    dealer more likely to bust when showing weak cards (2-6)
    standing on stiff hands (12-16) becomes more favorable
    """
    player_value = game.player_hand.get_value()
    dealer_up_card = game.dealer_hand.cards[0]
    
    # get dealer up card value
    if dealer_up_card.rank in ['J', 'Q', 'K']:
        dealer_value = 10
    elif dealer_up_card.rank == 'A':
        dealer_value = 11
    else:
        dealer_value = int(dealer_up_card.rank)
    
    ########################################################################

    # this part is unique to card counting vs basic strategy
    
    # calculate true count using actual remaining deck size
    if hasattr(game.deck, 'cards_remaining'):
        cards_left = game.deck.cards_remaining()
        decks_remaining = max(cards_left / 52, 0.5)
        true_count = counter.get_true_count(decks_remaining)
    else:
        true_count = counter.get_true_count()
    
    ########################################################################
    
    # check for soft hand (hands with an ace counted as 11)
    has_ace = any(card.rank == 'A' for card in game.player_hand.cards)
    is_soft = False

    # verify if we have a soft hand (ace still counted as 11, not forced to 1)
    if has_ace:
        # calculate what value would be if all aces were 1
        hard_value = sum(10 if c.rank in ['J','Q','K'] else (1 if c.rank == 'A' else int(c.rank)) 
                        for c in game.player_hand.cards)
        # if current value differs from hard value, we have a soft hand
        is_soft = (player_value != hard_value) and player_value <= 21
    
    # soft hand strategy (ace counted as 11)
    if is_soft:
        if player_value >= 19: # soft 19-21
            return 'stand'
        elif player_value == 18: # soft 18
            # hit against strong dealer cards
            if dealer_value in [9, 10, 11]:
                return 'hit'
            return 'stand'
        else: # soft 17 or less
            return 'hit'
    
    # hard hand strategy with count-based index plays
    # these are the key adjustments that give card counters their edge
    
    # hard hand strategy (ace counted as 1)
    if player_value >= 17:
        return 'stand'
    elif player_value <= 11:
        return 'hit' # always safe to hit, cant bust
    
    ########################################################################
    
    # the critical "index plays" - adjustments based on true count
    elif player_value == 16:
        if dealer_value <= 6:
            return 'stand' # dealer weak, always stand
        elif dealer_value in [7, 8]:
            return 'hit' # must improve vs dealer made hand
        elif dealer_value == 9:
            #16 vs 9 stand instead of hit at high true count (deck has lot of high cards)
            if true_count >= 5:
                return 'stand'
            return 'hit'
        else: # dealer has 10 or ace
            # if dealer has a 10 or ace and gets another 10, he beats you, so only stand if very sure there are few 10s left (positive high true)
            if true_count >= 0:
                return 'stand' # deck is neutral or rich in high cards
            return 'hit' # deck is poor in high cards
    
    elif player_value == 15:
        if dealer_value in [2, 3, 4, 5, 6]:
            return 'stand' # dealer weak
        elif dealer_value == 10:
            # stand on 15 vs 10 at true count +4 or higher
            if true_count >= 4:
                return 'stand' # very high count
            return 'hit'
        else:
            return 'hit'
    
    elif player_value == 14:
        # stand when dealer shows 2-6 (likely to bust)
        if dealer_value in [2, 3, 4, 5, 6]:
            return 'stand'
        return 'hit'
    
    elif player_value == 13:
        if dealer_value == 2:
            # 13 vs 2 hit instead of stand at low true count
            if true_count <= -1:
                return 'hit'
            return 'stand'
        elif dealer_value == 3:
            # 13 vs 3 hit instead of stand at low true count
            if true_count <= -2:
                return 'hit'
            return 'stand'
        elif dealer_value in [4, 5, 6]:
            return 'stand'
        else:
            return 'hit'
    
    elif player_value == 12:
        if dealer_value == 4:
            # 12 vs 4 hit instead of stand at low true count
            if true_count <= 0:
                return 'hit'
            return 'stand'
        elif dealer_value == 5:
            # 12 vs 5 hit instead of stand at very low true count
            if true_count <= -5:
                return 'hit'
            return 'stand'
        elif dealer_value == 6:
            # 12 vs 6 hit instead of stand at low true count
            if true_count <= -1:
                return 'hit'
            return 'stand'
        elif dealer_value == 3:
            # 12 vs 3 stand at true count +2 or higher
            if true_count >= 2:
                return 'stand'
            return 'hit'
        elif dealer_value == 2:
            # 12 vs 2 stand at true count +3 or higher
            if true_count >= 3:
                return 'stand'
            return 'hit'
        else:
            return 'hit'
    
    ########################################################################
    
    # default case
    return 'stand'
