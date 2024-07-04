from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.action import Action


class KnightAction(Action):
    CARD = Cards.KNIGHT

    def calculate_score(self, state):
        score = [0.5] if state.numbers["elixir"]["number"] == 10 else [0]
        for v in state.enemies.values():
            for position in v["positions"]:
                lhs = position.tile_x <= 8 and self.tile_x == 8
                rhs = position.tile_x > 8 and self.tile_x == 9

                if self.tile_y < position.tile_y <= 14 and (lhs or rhs):
                    score = [1, self.tile_y - position.tile_y]
        return score