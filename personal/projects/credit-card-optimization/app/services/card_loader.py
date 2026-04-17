"""Card database loader — registry-pattern ABC with JSON implementation.

The loader is the single point of card data access. It loads and validates
card records and store MCC mappings from static JSON files at startup.
"""

import abc
import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.models.card import CardRecord, StoreMccEntry

logger = logging.getLogger(__name__)


class CardDatabaseLoaderBase(abc.ABC):
    """Abstract base for card database loaders."""

    @abc.abstractmethod
    def load(self, cards_path: Path, store_mcc_path: Path) -> None:
        """Load and validate card data from the given paths."""

    @abc.abstractmethod
    def get_all(self) -> list[CardRecord]:
        """Return all loaded card records."""

    @abc.abstractmethod
    def get_by_id(self, card_id: str) -> CardRecord | None:
        """Return a card by its id, or None if not found."""

    @abc.abstractmethod
    def get_store_mcc_map(self) -> dict[str, StoreMccEntry]:
        """Return the store slug → StoreMccEntry mapping."""


class JsonCardDatabaseLoader(CardDatabaseLoaderBase):
    """Loads card data from static JSON files on disk."""

    def __init__(self) -> None:
        self._cards: list[CardRecord] = []
        self._cards_by_id: dict[str, CardRecord] = {}
        self._store_mcc_map: dict[str, StoreMccEntry] = {}

    def load(self, cards_path: Path, store_mcc_path: Path) -> None:
        """Load and validate cards and store MCC map from JSON files.

        Raises ValueError if any card record fails Pydantic validation
        (includes the offending card's id in the message) or if the
        JSON structure is invalid.
        """
        self._load_cards(cards_path)
        self._load_store_mcc_map(store_mcc_path)

    def _load_cards(self, cards_path: Path) -> None:
        try:
            raw = json.loads(cards_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Failed to read cards file {cards_path}: {exc}") from exc

        if not isinstance(raw, dict) or "cards" not in raw:
            raise ValueError(
                f"Invalid cards file structure in {cards_path}: "
                "expected top-level object with 'cards' array"
            )

        cards: list[CardRecord] = []
        cards_by_id: dict[str, CardRecord] = {}

        for i, card_dict in enumerate(raw["cards"]):
            card_id = card_dict.get("id", f"<index {i}>")
            try:
                card = CardRecord.model_validate(card_dict)
            except ValidationError as exc:
                raise ValueError(
                    f"Card validation failed for '{card_id}': {exc}"
                ) from exc
            cards.append(card)
            cards_by_id[card.id] = card

        self._cards = cards
        self._cards_by_id = cards_by_id
        logger.info("Loaded %d cards from %s", len(cards), cards_path)

    def _load_store_mcc_map(self, store_mcc_path: Path) -> None:
        try:
            raw = json.loads(store_mcc_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(
                f"Failed to read store MCC map {store_mcc_path}: {exc}"
            ) from exc

        store_map: dict[str, StoreMccEntry] = {}
        for slug, entry_dict in raw.items():
            try:
                store_map[slug] = StoreMccEntry.model_validate(entry_dict)
            except ValidationError as exc:
                raise ValueError(
                    f"Store MCC map validation failed for '{slug}': {exc}"
                ) from exc

        self._store_mcc_map = store_map
        logger.info(
            "Loaded %d store MCC entries from %s", len(store_map), store_mcc_path
        )

    def get_all(self) -> list[CardRecord]:
        return list(self._cards)

    def get_by_id(self, card_id: str) -> CardRecord | None:
        return self._cards_by_id.get(card_id)

    def get_store_mcc_map(self) -> dict[str, StoreMccEntry]:
        return dict(self._store_mcc_map)
