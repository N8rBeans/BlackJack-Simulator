import random
from typing import List, Tuple, Optional

class Card:
    """represents a single playing card with a suit and rank"""
    
    def __init__(self, suit: str, rank: str):
        """
        initialize a card with suit and rank
        suit: card suit symbol (♠, ♥, ♦, ♣)
        rank: card rank (2-10, J, Q, K, A)
        """
        self.suit = suit
        self.rank = rank
    
    def __str__(self):
        """return string representation of card (e.g., 'A♠')"""
        return f"{self.rank}{self.suit}"
    
    def value(self) -> int:
        """
        return the blackjack value of the card
        face cards (J, Q, K) are worth 10
        aces are worth 11 (adjusted later in hand if needed)
        number cards are worth their face value
        """
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11  # aces start at 11, can be reduced to 1 in Hand.get_value()
        else:
            return int(self.rank)

class Deck:
    """represents a deck (or shoe) of playing cards"""
    
    def __init__(self, num_decks: int = 1):
        """
        create and shuffle a deck or shoe
        num_decks: number of 52-card decks to combine (1 for single deck, 6-8 for casino shoe)
        """
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        # create all combinations of suits and ranks, multiplied by number of decks
        self.cards = [Card(suit, rank) for _ in range(num_decks) 
                      for suit in suits for rank in ranks]
        self.num_decks = num_decks
        self.total_cards = len(self.cards)
        self.shuffle()
    
    def shuffle(self):
        """randomly shuffle the deck/shoe"""
        random.shuffle(self.cards)
    
    def deal(self, counter=None) -> Card:
        """remove and return the top card from the deck"""
        card = self.cards.pop()
        if counter:
            counter.update(card)
        return card
    
    def cards_remaining(self) -> int:
        """return number of cards left in the deck"""
        return len(self.cards)
    
    def penetration(self) -> float:
        """
        return percentage of cards dealt (penetration)
        higher penetration = better for card counting
        """
        return (self.total_cards - len(self.cards)) / self.total_cards * 100
    
    def needs_shuffle(self, threshold: float = 75.0) -> bool:
        """
        check if deck needs reshuffling
        threshold: reshuffle when this percentage of cards have been dealt
        (casinos typically reshuffle at 70-80% penetration)
        """
        return self.penetration() >= threshold

class Hand:
    """represents a blackjack hand (collection of cards)"""
    
    def __init__(self):
        """initialize an empty hand"""
        self.cards: List[Card] = []
    
    def add_card(self, card: Card):
        """add a card to this hand"""
        self.cards.append(card)
    
    def get_value(self) -> int:
        """
        calculate the total value of the hand
        handles aces intelligently: treats them as 11 unless that would bust,
        then converts them to 1 as needed
        """
        # start by summing all cards at their initial values
        value = sum(card.value() for card in self.cards)
        # count how many aces we have
        aces = sum(1 for card in self.cards if card.rank == 'A')
        
        # if over 21 and have aces, convert them from 11 to 1
        # subtracting 10 is equivalent to changing an ace from 11 to 1
        while value > 21 and aces:
            value -= 10
            aces -= 1
        
        return value
    
    def is_blackjack(self) -> bool:
        """check if hand is a natural blackjack (21 with exactly 2 cards)"""
        return len(self.cards) == 2 and self.get_value() == 21
    
    def is_bust(self) -> bool:
        """check if hand value exceeds 21"""
        return self.get_value() > 21
    
    def __str__(self):
        """return string showing all cards in hand"""
        return ' '.join(str(card) for card in self.cards)

class BlackjackGame:
    """manages a single game of blackjack"""
    
    def __init__(self, deck=None, counter=None):
        """
        initialize a new game
        deck: optional existing deck to use (for multi-hand sessions)
              if None, creates a new single-deck game
        """
        if deck is None:
            self.deck = Deck(num_decks=1)
            self.owns_deck = True
        else:
            self.deck = deck
            self.owns_deck = False
        
        self.counter = counter
        self.player_hand = Hand()
        self.dealer_hand = Hand()
    
    def deal_initial_cards(self):
        """
        deal the initial two cards to each player
        order: player, dealer, player, dealer (as in real blackjack)
        """
        # count player card 1
        self.player_hand.add_card(self.deck.deal(self.counter))
        # dealer up-card (visible) = count it
        self.dealer_hand.add_card(self.deck.deal(self.counter))
        # count player card 2
        self.player_hand.add_card(self.deck.deal(self.counter))
        # dealer hole-card (face-down) = do NOT count yet
        self.dealer_hand.add_card(self.deck.deal(None))
    
    def show_hands(self, hide_dealer_card: bool = True):
        """
        display current state of both hands
        hide_dealer_card: if True, only show dealer's first card (standard during player's turn)
        """
        # when revealing dealer cards, update counter for the previously unseen hole card
        if not hide_dealer_card and self.counter and len(self.dealer_hand.cards) >= 2:
            hole = self.dealer_hand.cards[1]
            # only update if the counter hasnt seen this card yet
            self.counter.update(hole)
        
        print(f"\nDealer's hand: {self.dealer_hand.cards[0]}", end='')
        if hide_dealer_card:
            print(" ??")  # hide dealers second card
        else:
            # show all dealer cards and total
            print(f" {' '.join(str(c) for c in self.dealer_hand.cards[1:])}")
            print(f"Dealer's total: {self.dealer_hand.get_value()}")
        
        # always show all player cards and total
        print(f"Your hand: {self.player_hand}")
        print(f"Your total: {self.player_hand.get_value()}")
    
    def player_turn(self, get_action) -> bool:
        """
        handle the player's turn
        get_action: function that takes the game and returns 'hit' or 'stand'
        returns: True if player didn't bust, False if they busted
        """
        while True:
            # get player action (hit or stand) from the provided function
            action = get_action(self)
            
            if action == 'hit':
                # deal one card to player
                self.player_hand.add_card(self.deck.deal(self.counter))
                print(f"\nYou drew: {self.player_hand.cards[-1]}")
                print(f"Your total: {self.player_hand.get_value()}")
                
                # check if player busted
                if self.player_hand.is_bust():
                    print("Bust! You lose.")
                    return False
            elif action == 'stand':
                # player is done, move to dealer turn
                return True
            else:
                print("Invalid action. Use 'hit' or 'stand'")
    
    def dealer_turn(self):
        """
        handle dealer's turn following standard casino rules
        dealer must hit on 16 or less, must stand on 17 or more
        returns: True if dealer busted, False otherwise
        """
        print("\nDealer's turn...")
        self.show_hands(hide_dealer_card=False)  # reveal dealer hidden card
        
        # dealer keeps hitting until reaching 17 or higher
        while self.dealer_hand.get_value() < 17:
            card = self.deck.deal(self.counter)
            self.dealer_hand.add_card(card)
            print(f"Dealer draws: {card}")
            print(f"Dealer's total: {self.dealer_hand.get_value()}")
        
        # check if dealer busted
        if self.dealer_hand.is_bust():
            print("Dealer busts! You win!")
            return True
        
        return False
    
    def determine_winner(self):
        """
        compare final hands and announce the winner
        handles special cases like blackjack and ties
        """
        player_val = self.player_hand.get_value()
        dealer_val = self.dealer_hand.get_value()
        
        # check for natural blackjacks (wins pay more in real casinos)
        if self.player_hand.is_blackjack() and not self.dealer_hand.is_blackjack():
            print("Blackjack! You win!")
        elif self.dealer_hand.is_blackjack() and not self.player_hand.is_blackjack():
            print("Dealer has Blackjack. You lose.")
        # compare hand values
        elif player_val > dealer_val:
            print("You win!")
        elif player_val < dealer_val:
            print("Dealer wins.")
        else:
            print("Push (tie).")  # push means tie, no one wins
    
    def play(self, get_action=None):
        """
        play a complete game of blackjack
        get_action: function that takes the game state and returns 'hit' or 'stand'
                   if None, uses terminal input for human player
        """
        # use terminal input if no custom action function provided
        if get_action is None:
            get_action = self.get_terminal_action
        
        # deal initial cards (2 to each player)
        self.deal_initial_cards()
        
        print("=" * 40)
        print("BLACKJACK")
        print("=" * 40)
        
        self.show_hands()  # show hands with dealer second card hidden
        
        # check if either player has a natural blackjack
        if self.player_hand.is_blackjack() or self.dealer_hand.is_blackjack():
            # reveal dealer's cards and determine winner immediately
            self.show_hands(hide_dealer_card=False)
            self.determine_winner()
            return
        
        # player turn: hit or stand until bust or stand
        if not self.player_turn(get_action):
            return  # player busted, game over
        
        # dealer turn: hit until 17+ following casino rules
        if self.dealer_turn():
            return  # dealer busted, player wins
        
        # both players still in: compare hands to determine winner
        self.show_hands(hide_dealer_card=False)
        self.determine_winner()
    
    @staticmethod
    def get_terminal_action(game) -> str:
        """
        get player action from terminal input
        prompts user to enter 'h' or 's' for hit or stand
        """
        while True:
            action = input("\nDo you want to (h)it or (s)tand? ").lower()
            if action in ['h', 'hit']:
                return 'hit'
            elif action in ['s', 'stand']:
                return 'stand'
            else:
                print("Please enter 'h' or 's'")

def main():
    """main game loop: play games until user wants to quit"""
    while True:
        # create and play a new game
        game = BlackjackGame()
        game.play()
        
        # ask if player wants another round
        play_again = input("\nPlay again? (y/n): ").lower()
        if play_again not in ['y', 'yes']:
            print("Thanks for playing!")
            break

if __name__ == "__main__":
    main()