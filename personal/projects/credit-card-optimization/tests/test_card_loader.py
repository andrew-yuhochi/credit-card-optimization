"""Tests for app.services.card_loader — JsonCardDatabaseLoader."""

import json
from pathlib import Path

import pytest

from app.models.card import CardRecord, StoreMccEntry
from app.services.card_loader import CardDatabaseLoaderBase, JsonCardDatabaseLoader

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CARDS_PATH = DATA_DIR / "cards" / "cards.json"
STORE_MCC_PATH = DATA_DIR / "stores" / "store_mcc_map.json"


# --- fixtures ---


@pytest.fixture()
def loader() -> JsonCardDatabaseLoader:
    """A loader pre-loaded with the real seed data."""
    ldr = JsonCardDatabaseLoader()
    ldr.load(CARDS_PATH, STORE_MCC_PATH)
    return ldr


@pytest.fixture()
def tmp_cards_file(tmp_path: Path) -> Path:
    """Path to a temporary cards JSON file."""
    return tmp_path / "cards.json"


@pytest.fixture()
def tmp_store_file(tmp_path: Path) -> Path:
    """Path to a temporary store MCC map JSON file."""
    p = tmp_path / "store_mcc_map.json"
    p.write_text(json.dumps({
        "test_store": {"mcc": "5411", "default_category": "grocery"}
    }))
    return p


@pytest.fixture()
def valid_card_dict() -> dict:
    return {
        "id": "test_card",
        "name": "Test Card",
        "issuer": "TestBank",
        "network": "Visa",
        "annual_fee": 0.0,
        "first_year_fee": 0.0,
        "requires_amex": False,
        "approval": {
            "min_credit_score": 600,
            "min_personal_income": 30000,
            "min_household_income": 50000,
            "source": "estimated",
            "confidence": "low",
        },
        "category_rates": {"other": 1.0},
        "point_system": "cashback",
        "cpp_default": 1.0,
        "last_verified_date": "2026-01-01",
        "source_url": "https://example.com",
    }


# --- ABC ---


class TestCardDatabaseLoaderBase:
    def test_is_abstract(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            CardDatabaseLoaderBase()


# --- Loading seed data ---


class TestJsonCardDatabaseLoaderSeedData:
    def test_loads_all_seed_cards(self, loader: JsonCardDatabaseLoader) -> None:
        cards = loader.get_all()
        assert len(cards) == 5
        assert all(isinstance(c, CardRecord) for c in cards)

    def test_get_by_id_cibc(self, loader: JsonCardDatabaseLoader) -> None:
        card = loader.get_by_id("cibc_dividend_vi")
        assert card is not None
        assert card.name == "CIBC Dividend Visa Infinite"
        assert card.issuer == "CIBC"

    def test_get_by_id_all_seeds(self, loader: JsonCardDatabaseLoader) -> None:
        expected_ids = [
            "cibc_dividend_vi",
            "scotiabank_gold_amex",
            "pc_financial_we_mc",
            "rogers_red_we_mc",
            "amex_cobalt",
        ]
        for card_id in expected_ids:
            assert loader.get_by_id(card_id) is not None, f"Missing: {card_id}"

    def test_get_by_id_nonexistent(self, loader: JsonCardDatabaseLoader) -> None:
        assert loader.get_by_id("nonexistent") is None

    def test_get_all_returns_copy(self, loader: JsonCardDatabaseLoader) -> None:
        cards1 = loader.get_all()
        cards2 = loader.get_all()
        assert cards1 is not cards2
        assert cards1 == cards2

    def test_store_mcc_map(self, loader: JsonCardDatabaseLoader) -> None:
        store_map = loader.get_store_mcc_map()
        assert len(store_map) == 8
        assert all(isinstance(v, StoreMccEntry) for v in store_map.values())

    def test_store_mcc_map_costco(self, loader: JsonCardDatabaseLoader) -> None:
        store_map = loader.get_store_mcc_map()
        costco = store_map["costco"]
        assert costco.mcc == "5300"
        assert costco.default_category == "wholesale"

    def test_store_mcc_map_returns_copy(self, loader: JsonCardDatabaseLoader) -> None:
        map1 = loader.get_store_mcc_map()
        map2 = loader.get_store_mcc_map()
        assert map1 is not map2

    def test_store_mcc_map_keys(self, loader: JsonCardDatabaseLoader) -> None:
        expected = {
            "costco", "walmart", "shoppers_drug_mart", "canadian_tire",
            "loblaws", "amazon_ca", "lcbo", "lowes",
        }
        assert set(loader.get_store_mcc_map().keys()) == expected


# --- Error handling ---


class TestJsonCardDatabaseLoaderErrors:
    def test_missing_cards_file(self, tmp_path: Path, tmp_store_file: Path) -> None:
        ldr = JsonCardDatabaseLoader()
        with pytest.raises(ValueError, match="Failed to read cards file"):
            ldr.load(tmp_path / "does_not_exist.json", tmp_store_file)

    def test_malformed_json(
        self, tmp_path: Path, tmp_store_file: Path
    ) -> None:
        bad = tmp_path / "cards.json"
        bad.write_text("{not valid json")
        ldr = JsonCardDatabaseLoader()
        with pytest.raises(ValueError, match="Failed to read cards file"):
            ldr.load(bad, tmp_store_file)

    def test_missing_cards_key(
        self, tmp_path: Path, tmp_store_file: Path
    ) -> None:
        bad = tmp_path / "cards.json"
        bad.write_text(json.dumps({"schema_version": "1.0"}))
        ldr = JsonCardDatabaseLoader()
        with pytest.raises(ValueError, match="expected top-level object with 'cards' array"):
            ldr.load(bad, tmp_store_file)

    def test_invalid_card_record(
        self,
        tmp_path: Path,
        tmp_store_file: Path,
        valid_card_dict: dict,
    ) -> None:
        bad_card = {**valid_card_dict, "id": "bad_card", "network": "Discover"}
        cards_file = tmp_path / "cards.json"
        cards_file.write_text(json.dumps({
            "schema_version": "1.0",
            "cards": [valid_card_dict, bad_card],
        }))
        ldr = JsonCardDatabaseLoader()
        with pytest.raises(ValueError, match="Card validation failed for 'bad_card'"):
            ldr.load(cards_file, tmp_store_file)

    def test_invalid_card_no_id(
        self, tmp_path: Path, tmp_store_file: Path
    ) -> None:
        cards_file = tmp_path / "cards.json"
        cards_file.write_text(json.dumps({
            "schema_version": "1.0",
            "cards": [{"name": "broken"}],
        }))
        ldr = JsonCardDatabaseLoader()
        with pytest.raises(ValueError, match="Card validation failed for '<index 0>'"):
            ldr.load(cards_file, tmp_store_file)

    def test_missing_store_mcc_file(self, tmp_path: Path, valid_card_dict: dict) -> None:
        cards_file = tmp_path / "cards.json"
        cards_file.write_text(json.dumps({
            "schema_version": "1.0",
            "cards": [valid_card_dict],
        }))
        ldr = JsonCardDatabaseLoader()
        with pytest.raises(ValueError, match="Failed to read store MCC map"):
            ldr.load(cards_file, tmp_path / "missing.json")

    def test_invalid_store_mcc_entry(
        self, tmp_path: Path, valid_card_dict: dict
    ) -> None:
        cards_file = tmp_path / "cards.json"
        cards_file.write_text(json.dumps({
            "schema_version": "1.0",
            "cards": [valid_card_dict],
        }))
        store_file = tmp_path / "store_mcc_map.json"
        store_file.write_text(json.dumps({
            "bad_store": {"not_mcc": "1234"},
        }))
        ldr = JsonCardDatabaseLoader()
        with pytest.raises(ValueError, match="Store MCC map validation failed for 'bad_store'"):
            ldr.load(cards_file, store_file)


# --- Loading custom data ---


class TestJsonCardDatabaseLoaderCustomData:
    def test_single_card(
        self,
        tmp_cards_file: Path,
        tmp_store_file: Path,
        valid_card_dict: dict,
    ) -> None:
        tmp_cards_file.write_text(json.dumps({
            "schema_version": "1.0",
            "cards": [valid_card_dict],
        }))
        ldr = JsonCardDatabaseLoader()
        ldr.load(tmp_cards_file, tmp_store_file)
        assert len(ldr.get_all()) == 1
        assert ldr.get_by_id("test_card") is not None

    def test_empty_cards_list(
        self, tmp_cards_file: Path, tmp_store_file: Path
    ) -> None:
        tmp_cards_file.write_text(json.dumps({
            "schema_version": "1.0",
            "cards": [],
        }))
        ldr = JsonCardDatabaseLoader()
        ldr.load(tmp_cards_file, tmp_store_file)
        assert len(ldr.get_all()) == 0
        assert ldr.get_by_id("anything") is None

    def test_reload_replaces_data(
        self,
        tmp_path: Path,
        tmp_store_file: Path,
        valid_card_dict: dict,
    ) -> None:
        cards_file = tmp_path / "cards.json"
        cards_file.write_text(json.dumps({
            "schema_version": "1.0",
            "cards": [valid_card_dict],
        }))
        ldr = JsonCardDatabaseLoader()
        ldr.load(cards_file, tmp_store_file)
        assert len(ldr.get_all()) == 1

        card2 = {**valid_card_dict, "id": "card_two", "name": "Card Two"}
        cards_file.write_text(json.dumps({
            "schema_version": "1.0",
            "cards": [valid_card_dict, card2],
        }))
        ldr.load(cards_file, tmp_store_file)
        assert len(ldr.get_all()) == 2
        assert ldr.get_by_id("card_two") is not None
