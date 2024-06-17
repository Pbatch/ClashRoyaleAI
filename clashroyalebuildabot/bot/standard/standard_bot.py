import random
import time

from clashroyalebuildabot.bot.bot import Bot
from clashroyalebuildabot.bot.standard.standard_action import StandardAction
from clashroyalebuildabot.data.cards import Cards
from clashroyalebuildabot.data.constants import DISPLAY_HEIGHT
from clashroyalebuildabot.data.constants import DISPLAY_WIDTH
from clashroyalebuildabot.data.constants import SCREENSHOT_HEIGHT
from clashroyalebuildabot.data.constants import SCREENSHOT_WIDTH


class StandardBot(Bot):
    def __init__(self, card_names, debug=False):
        preset_deck = {
            Cards.MINIONS,
            Cards.ARCHERS,
            Cards.ARROWS,
            Cards.GIANT,
            Cards.MINIPEKKA,
            Cards.FIREBALL,
            Cards.KNIGHT,
            Cards.MUSKETEER,
        }
        if set(card_names) != preset_deck:
            raise ValueError(
                f"You must use the preset deck with cards {preset_deck} for StandardBot"
            )
        super().__init__(card_names, StandardAction, debug=debug)

    def _preprocess(self):
        """
        Perform preprocessing on the state

        Estimate the tile of each unit to be the bottom of their bounding box
        """
        for side in ["ally", "enemy"]:
            for k, v in self.state["units"][side].items():
                for unit in v["positions"]:
                    bbox = unit["bounding_box"]
                    bbox[0] *= DISPLAY_WIDTH / SCREENSHOT_WIDTH
                    bbox[1] *= DISPLAY_HEIGHT / SCREENSHOT_HEIGHT
                    bbox[2] *= DISPLAY_WIDTH / SCREENSHOT_WIDTH
                    bbox[3] *= DISPLAY_HEIGHT / SCREENSHOT_HEIGHT
                    bbox_bottom = [((bbox[0] + bbox[2]) / 2), bbox[3]]
                    unit["tile_xy"] = self._get_nearest_tile(*bbox_bottom)

    def run(self):
        while True:
            # Set the state of the game
            self.set_state()
            # Obtain a list of playable actions
            actions = self.get_actions()
            if actions:
                # Shuffle the actions (because action scores might be the same)
                random.shuffle(actions)
                # Preprocessing
                self._preprocess()
                # Get the best action
                action = max(
                    actions, key=lambda x: x.calculate_score(self.state)
                )
                # Skip the action if it doesn't score high enough
                if action.score[0] == 0:
                    continue
                # Play the best action
                self.play_action(action)
                # Log the result
                print(
                    f"Playing {action} with score {action.score} and sleeping for 1 second"
                )
                time.sleep(0.5)
