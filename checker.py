import numpy as np
from player import Player


# Fair strategy
class Checker(Player):

    def __init__(self, name):
        super().__init__(name)

        self.game_started = False
        self.I_checked = False

        self.my_cards_on_pile = []
        self.my_cards_known_by_him = []

        self.known_opponent_cards = []
        self.opponent_cards_number = 8

        self.stack_size = 0

        self.whole_deck = [(number, color) for color in range(4) for number in range(9, 15)]

        self.number_of_moves = 0
        self.number_of_opponents_lies = 0
        self.number_of_opponents_checks = 0

    def action_for_opponent_draw(self):
        my_cards_taken = 2 if self.stack_size >= 3 else 1
        his_cards_taken = 1 if self.stack_size >= 2 else 0
        self.known_opponent_cards += self.my_cards_on_pile[my_cards_taken:]
        self.opponent_cards_number += his_cards_taken + my_cards_taken
        self.my_cards_on_pile = self.my_cards_on_pile[:-my_cards_taken]
        self.stack_size -= my_cards_taken + his_cards_taken

    def play_card(self, card, decision=None):
        if decision is None:
            decision = card
        self.my_cards_on_pile.append(card)
        decision = card, card
        return decision
    
    def card_to_lie(self, declared_card):
        whole_set = set(self.whole_deck)
        my_set = set(self.cards)
        opponent_set = set(self.known_opponent_cards)
        my_pile_set = set(self.my_cards_on_pile)
        possible_cards = list(whole_set - my_set - opponent_set - my_pile_set)
        possible_cards = [x for x in possible_cards if x[0] >= declared_card[0]]
        chosen_idx = np.random.randint(len(possible_cards))
        return possible_cards[chosen_idx]
    
    def putCard(self, declared_card):
        # Sort cards
        self.cards = sorted(
            self.cards, key=lambda x: x[0]) if self.cards is not None else None
        self.known_opponent_cards = list(set(self.known_opponent_cards))

        self.number_of_moves += 1

        # Start the decision with None
        decision = None

        # If the opponent declared None we have 2 options
        if declared_card is None:
            # Either I'm starting the game
            if not self.game_started:
                self.game_started = True
            # Or he's drawn cards
            else:
                # If the opponent drew
                if not self.I_checked:
                    self.action_for_opponent_draw()

            # Either way I'm just correctly putting my lowest card
            decision = self.play_card(self.cards[0])

        # If the opponent declared a card we have 3 options
        else:
            # The game may start with the opponent declaration
            if not self.game_started:
                self.game_started = True

            # He put one card
            self.opponent_cards_number -= 1
            self.stack_size += 1
            if declared_card in self.known_opponent_cards:
                self.known_opponent_cards.remove(declared_card)

            # If a have a correct card I'm just putting it
            for card in self.cards:
                if card[0] >= declared_card[0]:
                    decision = self.play_card(card)
                    break

        # If there's no choice made 'll just draw
        if decision is None:
            decision = "draw"
            cards_to_take = min(3, self.stack_size)
            self.stack_size -= cards_to_take
            self.my_cards_on_pile = self.my_cards_on_pile[:-cards_to_take]

        else:
            self.stack_size += 1

        return decision

    def make_check_decision(self, bool):
        self.I_checked = bool
        decision = bool
        return decision
    
    def checkCard(self, opponent_declaration):
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
        else:
            # I know that number of cards - too less knowledge
            # known_cards = len(
            #     self.cards) + len(self.my_cards_on_pile) + len(self.known_opponent_cards)
            # card_probability = 1 / (24-known_cards)

            # NEVER CHECK

            check_prop = np.random.uniform(0, 1)
            check_prop *= 1 - self.number_of_opponents_lies / (self.number_of_moves + 1)
            
            if check_prop > 0.7:
                decision = True
            else:
                decision = False

            self.I_checked = decision

        return decision

    def get_his_my_cards_taken(self, checked, iChecked):
        if checked and iChecked:
            his_cards_taken = 2 if self.stack_size >= 3 else 1
            my_cards_taken = 1 if self.stack_size >= 2 else 0
        elif checked and not iChecked:
            my_cards_taken = 2 if self.stack_size >= 3 else 1
            his_cards_taken = 1 if self.stack_size >= 2 else 0
        else:
            my_cards_taken = 0
            his_cards_taken = 0
        return his_cards_taken, my_cards_taken
    
    def getCheckFeedback(self, checked, iChecked, iDrewCards, revealedCard, noTakenCards, log=False):
        # I checked correctly
        his_cards_taken, my_cards_taken = self.get_his_my_cards_taken(checked, iChecked)
        if checked and revealedCard is not None and iChecked and not iDrewCards:
            #as he firstly puts
            self.stack_size += 1
            self.stack_size -= noTakenCards

            self.known_opponent_cards.append(revealedCard)
            if len(self.my_cards_on_pile)>0:
                self.known_opponent_cards.append(self.my_cards_on_pile[-1])

            self.opponent_cards_number += noTakenCards - 1

            self.my_cards_on_pile = self.my_cards_on_pile[:-my_cards_taken] if len(self.my_cards_on_pile)>0 else []

            self.number_of_opponents_lies += 1

        # I checked incorrectly
        if checked and iChecked and iDrewCards:
            #as he firstly puts
            self.stack_size += 1
            self.stack_size -= noTakenCards

            self.my_cards_on_pile = self.my_cards_on_pile[:-my_cards_taken]

        # he checked correctly
        if checked and not iChecked and iDrewCards:
            self.stack_size -= noTakenCards

            self.my_cards_on_pile = self.my_cards_on_pile[:-my_cards_taken]

            self.number_of_opponents_checks += 1
        
        # he checked incorrectly
        if checked and not iChecked and not iDrewCards:
            self.known_opponent_cards += self.my_cards_on_pile[my_cards_taken:]

            # assert noTakenCards == his_cards_taken + my_cards_taken
            self.opponent_cards_number += his_cards_taken + my_cards_taken

            self.my_cards_on_pile = self.my_cards_on_pile[:-my_cards_taken]

            self.stack_size -= noTakenCards

            self.number_of_opponents_checks += 1

            