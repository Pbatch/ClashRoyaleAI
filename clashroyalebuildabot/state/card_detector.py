import os
from PIL import Image
import numpy as np
from clashroyalebuildabot.data.constants import (
    CARD_CONFIG,
    DATA_DIR,
    MULTI_HASH_SCALE,
    MULTI_HASH_INTERCEPT,
    DECK_SIZE,
    HAND_SIZE,
)
from scipy.optimize import linear_sum_assignment


class CardDetector:
    def __init__(self, card_names, hash_size=8, grey_std_threshold=5):
        self.card_names = card_names
        self.hash_size = hash_size
        self.grey_std_threshold = grey_std_threshold
        self.cards, self.card_hashes = self._calculate_cards_and_card_hashes()

    def _calculate_multi_hash(self, image):
        gray_image = self._calculate_hash(image)
        light_image = MULTI_HASH_SCALE * gray_image + MULTI_HASH_INTERCEPT
        dark_image = (gray_image - MULTI_HASH_INTERCEPT) / MULTI_HASH_SCALE
        multi_hash = np.vstack([gray_image, light_image, dark_image]).astype(
            np.float32
        )
        return multi_hash

    def _calculate_hash(self, image):
        return np.array(
            image.resize(
                (self.hash_size, self.hash_size), Image.BILINEAR
            ).convert("L"),
            dtype=np.float32,
        ).ravel()

    def _calculate_cards_and_card_hashes(self):
        cards = []
        card_hashes = np.zeros(
            (DECK_SIZE + 1, 3, self.hash_size * self.hash_size, HAND_SIZE),
            dtype=np.float32,
        )
        i = 0
        with open(os.path.join(DATA_DIR, "cards.csv")) as f:
            for line in f:
                name, _, cost, type_, target, _ = (
                    line.strip().replace('"', "").split(",")
                )
                if name in self.card_names:
                    path = os.path.join(
                        DATA_DIR, "images", "cards", f"{name}.jpg"
                    )
                    card = Image.open(path)
                    multi_hash = self._calculate_multi_hash(card)
                    card_hashes[i] = np.tile(
                        np.expand_dims(multi_hash, axis=2), (1, 1, HAND_SIZE)
                    )
                    cards.append(
                        {
                            "name": name,
                            "cost": int(cost),
                            "type": type_,
                            "target": target,
                        }
                    )
                    i += 1
        path = os.path.join(DATA_DIR, "images", "cards", "blank.jpg")
        card = Image.open(path)
        multi_hash = self._calculate_multi_hash(card)
        card_hashes[-1] = np.tile(
            np.expand_dims(multi_hash, axis=2), (1, 1, HAND_SIZE)
        )
        cards.append(
            {"name": "blank", "cost": 11, "type": "n/a", "target": "n/a"}
        )
        return cards, card_hashes

    def _detect_cards(self, image):
        crops = [image.crop(position) for position in CARD_CONFIG]
        crop_hashes = np.array(
            [self._calculate_hash(crop) for crop in crops]
        ).T
        hash_diffs = np.mean(
            np.amin(np.abs(crop_hashes - self.card_hashes), axis=1), axis=1
        ).T
        _, idx = linear_sum_assignment(hash_diffs)
        cards = [self.cards[i] for i in idx]
        return cards, crops

    def _detect_if_ready(self, cards, crops):
        for card, crop in zip(cards, crops):
            std = np.mean(np.std(np.array(crop), axis=2))
            card["ready"] = std > self.grey_std_threshold
        return cards

    def run(self, image):
        cards, crops = self._detect_cards(image)
        cards = self._detect_if_ready(cards, crops)
        return cards
