import numpy as np
from player import Player


# Fair strategy
class CyganikChwilczynski(Player):

    def __init__(self, name: str) -> None:
        super().__init__(name)

        self.game_started = False
        self.I_checked = False

        self.whole_deck = [(number, color) for color in range(4)
                           for number in range(9, 15)]
        self.my_cards_on_pile = []
        self.my_cards_known_by_him = []
        self.known_opponent_cards = []

        self.opponent_cards_number = 8
        self.stack_size = 0
        self.check_prob = 0.05

    def action_for_opponent_draw(self) -> None:
        '''
        This function is called when the opponent draws cards.
        It firstly calculates the number ofmy and opponent's cards taken by the opponent.
        Then it adds my cards taken by the opponent to the list of his cards known by me.
        The it updates the number of opponent's cards and my cards on pile, as well as the stack size.
        '''

        his_cards_taken, my_cards_taken = self.get_his_my_cards_taken(
            True, False)
        self.known_opponent_cards += self.my_cards_on_pile[my_cards_taken:]
        self.opponent_cards_number += his_cards_taken + my_cards_taken
        self.my_cards_on_pile = self.my_cards_on_pile[:-my_cards_taken]
        self.stack_size -= my_cards_taken + his_cards_taken

    def play_card(self, card: tuple[int, int], declaration=None) -> tuple[tuple[int, int], tuple[int, int]]:
        '''
        This function is called when the player puts a card on the pile.
        It firstly adds the card to the list of cards on pile.
        Then it creates a decision which is a tuple of the card and its declaration.
        The declaration is the same as the card if it is not specified.
        '''

        if declaration is None:
            declaration = card
        self.my_cards_on_pile.append(card)
        decision = card, declaration
        return decision

    def card_to_lie(self, declared_card: tuple[int, int]) -> tuple[int, int] | None:
        '''
        This function is called when the player has to lie.
        It firstly creates a list of possible cards to lie.
        Then it chooses one of them randomly.
        If there is no possible card to lie, it returns None.
        '''

        whole_set = set(self.whole_deck)
        my_set = set(self.cards)
        opponent_set = set(self.known_opponent_cards)
        my_pile_set = set(self.my_cards_on_pile)
        possible_cards = list(whole_set - my_set - opponent_set - my_pile_set)
        possible_cards = [
            x for x in possible_cards if x[0] >= declared_card[0]]
        if len(possible_cards) == 0:
            return None
        chosen_idx = np.random.randint(len(possible_cards))
        return possible_cards[chosen_idx]

    def on_opponents_put(self, declared_card: tuple[int, int]) -> None:
        '''
        This function is called when the opponent puts a card on the pile.
        It firstly updates the number of opponent's cards and the stack size.
        Then it removes the card from the list of opponent's cards known by me.
        '''

        self.opponent_cards_number -= 1
        self.stack_size += 1
        if declared_card in self.known_opponent_cards:
            self.known_opponent_cards.remove(declared_card)

    def putCard(self, declared_card: tuple[int, int] | None) -> tuple[tuple[int, int], tuple[int, int]] | str:
        '''
        This is the main function called by the game engine.
        More detailed description of the strategy is above each move.
        '''

        # Sort cards
        self.cards = sorted(
            self.cards, key=lambda x: x[0]) if self.cards is not None else None
        self.known_opponent_cards = list(set(self.known_opponent_cards))

        # Start the decision with None
        decision = None

        # If the opponent declares None we have 2 options
        if declared_card is None:
            # Either I'm starting the game
            if not self.game_started:
                self.game_started = True
            # Or he's drawn cards
            else:
                self.action_for_opponent_draw()

            # Either way I'm just correctly putting my lowest card
            decision = self.play_card(self.cards[0])

        # If the opponent declares a card we have 3 options
        else:
            # The game may start with the opponent declaration
            if not self.game_started:
                self.game_started = True

            # He puts one card
            self.on_opponents_put(declared_card)

            # If a have a correct card I'm just putting it
            for card in self.cards:
                if card[0] >= declared_card[0]:
                    decision = self.play_card(card)
                    break

        # Lie always if you can't move properly
        if decision is None and len(self.cards) > 1:
            card_to_lie = self.card_to_lie(declared_card)
            if card_to_lie is not None:
                decision = self.play_card(
                    card, self.card_to_lie(declared_card))

        # If there's no choice made I'll just draw
        if decision is None:
            decision = "draw"
            cards_to_take = min(3, self.stack_size)
            self.stack_size -= cards_to_take
            self.my_cards_on_pile = self.my_cards_on_pile[:-cards_to_take]
        else:
            self.stack_size += 1

        return decision

    def make_check_decision(self, decision: bool) -> bool:
        self.I_checked = bool
        return decision

    def checkCard(self, opponent_declaration: tuple[int, int] | None) -> bool:
        '''
        This function is called when the player has to check the card.
        The detailed description of the strategy is above each move.
        '''

        # If the opponent declared None I'm not checking
        if opponent_declaration is None:
            decision = self.make_check_decision(False)
        # If the opponent declared a card I'm sure it's on pile I'm checking it
        elif opponent_declaration in self.my_cards_on_pile:
            decision = self.make_check_decision(True)
        # If the opponent declared a card which belongs to me I'm checking it
        elif opponent_declaration in self.cards:
            decision = self.make_check_decision(True)
        # If I know he has it, I don't want to check it
        elif opponent_declaration in self.known_opponent_cards:
            decision = self.make_check_decision(False)
        # If I don't know anything about the card I'm checking it with very low probability
        else:
            random_number = np.random.rand()
            if random_number < self.check_prob and len(self.cards) > self.opponent_cards_number+2:
                decision = True
            else:
                decision = False

            self.I_checked = decision

        return decision

    def get_his_my_cards_taken(self, checked: bool, iChecked: bool) -> tuple[int, int]:
        '''
        This function returns the number of my and the opponent's cards taken by the opponent.
        These numbers are calculated based on the stack size and the number of cards on the pile.
        If the stach has 0 cards, no cards are taken.
        If the stack has 1 card, the opponent takes 1 card. If I checked, than this card is his, otherwise it's mine.
        If the stack has 2 cards, the opponent takes 2 cards. If I checked, than these cards are 1 mine and 1 his, otherwise the opposite.
        If the stack has 3 or more cards, the opponent takes 3 cards. If I checked, than these cards are 2 hise and 1 mine, otherwise the opposite.
        '''

        if checked and iChecked:
            his_cards_taken = 2 if self.stack_size >= 3 else 1
            my_cards_taken = 1 if self.stack_size >= 2 else 0
        elif checked and not iChecked:
            my_cards_taken = 2 if self.stack_size >= 3 else 1
            his_cards_taken = 1 if self.stack_size >= 2 else 0
        else:
            my_cards_taken = 0
            his_cards_taken = 0
        if self.stack_size == 0:
            my_cards_taken = 0
            his_cards_taken = 0
        if len(self.my_cards_on_pile) == 0:
            my_cards_taken = 0
        return his_cards_taken, my_cards_taken

    def getCheckFeedback(self, checked: bool, iChecked: bool, iDrewCards: bool, revealedCard: tuple[int, int], noTakenCards: int, log=False) -> None:
        his_cards_taken, my_cards_taken = self.get_his_my_cards_taken(
            checked, iChecked)

        # I checked correctly
        if checked and revealedCard is not None and iChecked and not iDrewCards:
            # as he firstly puts
            self.stack_size += 1
            self.stack_size -= noTakenCards

            self.known_opponent_cards.append(revealedCard)

            if my_cards_taken > 0:
                self.known_opponent_cards.append(
                    self.my_cards_on_pile[-my_cards_taken])

            self.opponent_cards_number += noTakenCards - 1

            self.my_cards_on_pile = self.my_cards_on_pile[:-my_cards_taken]
            
            self.check_prob += (1 - self.check_prob) * 0.2

        # I checked incorrectly
        if checked and iChecked and iDrewCards:
            # as he firstly puts
            self.stack_size += 1
            self.stack_size -= noTakenCards

            self.my_cards_on_pile = self.my_cards_on_pile[:-my_cards_taken]

            self.check_prob -= (1 - self.check_prob) * 0.9

        # he checked correctly
        if checked and not iChecked and iDrewCards:
            self.stack_size -= noTakenCards

            self.my_cards_on_pile = self.my_cards_on_pile[:-my_cards_taken]

        # he checked incorrectly
        if checked and not iChecked and not iDrewCards:
            self.known_opponent_cards += self.my_cards_on_pile[my_cards_taken:]

            # assert noTakenCards == his_cards_taken + my_cards_taken
            self.opponent_cards_number += his_cards_taken + my_cards_taken

            self.my_cards_on_pile = self.my_cards_on_pile[:-my_cards_taken]

            self.stack_size -= noTakenCards
