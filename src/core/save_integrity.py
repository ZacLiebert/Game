"""Save-file integrity helpers."""

import hashlib
import hmac
import json
from pathlib import Path


class SaveEncryption:
    """Saves readable JSON with an HMAC signature to detect edits."""

    VERSION = 3
    ALGORITHM = "HMAC-SHA256"
    DEFAULT_SECRET_KEY = "UIT_MUTATION_SECRET"

    # HMAC helpers

    @staticmethod
    def _normalize_key(secret_key):
        """Convert the secret key to bytes."""
        if isinstance(secret_key, bytes):
            return secret_key

        return str(secret_key).encode("utf-8")

    @staticmethod
    def _serialize_data(data):
        """Convert save data to stable JSON bytes."""
        return json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":")
        ).encode("utf-8")

    @staticmethod
    def _create_hmac(data, secret_key):
        """Create the HMAC signature for save data."""
        key = SaveEncryption._normalize_key(secret_key)
        message = SaveEncryption._serialize_data(data)

        return hmac.new(
            key,
            message,
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _verify_hmac(data, received_hmac, secret_key):
        """Check whether the stored save signature matches."""
        expected_hmac = SaveEncryption._create_hmac(data, secret_key)

        return hmac.compare_digest(
            expected_hmac,
            str(received_hmac)
        )

    # Save / load API

    @staticmethod
    def save_game(save_dict, file_path, secret_key=DEFAULT_SECRET_KEY):
        """Write save data with an integrity signature."""
        file_path = Path(file_path)

        try:
            signature = SaveEncryption._create_hmac(
                save_dict,
                secret_key
            )

            save_container = {
                "version": SaveEncryption.VERSION,
                "algorithm": SaveEncryption.ALGORITHM,
                "data": save_dict,
                "hmac": signature
            }

            encoded_container = json.dumps(
                save_container,
                ensure_ascii=False,
                indent=2
            ).encode("utf-8")

            file_path.parent.mkdir(parents=True, exist_ok=True)

            with file_path.open("wb") as f:
                f.write(encoded_container)

            return True

        except Exception as e:
            print(f"Failed to save game. Error: {e}")
            return False

    @staticmethod
    def load_game(file_path, secret_key=DEFAULT_SECRET_KEY):
        """Load the game."""
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        try:
            with file_path.open("rb") as f:
                raw_data = f.read()

            try:
                save_container = json.loads(raw_data.decode("utf-8"))
            except Exception:
                print("Failed to load save file. Invalid JSON format.")
                return None

            if not isinstance(save_container, dict):
                print("Failed to load save file. Save container is invalid.")
                return None

            version = save_container.get("version")
            algorithm = save_container.get("algorithm")
            save_data = save_container.get("data")
            received_hmac = save_container.get("hmac")

            if version != SaveEncryption.VERSION:
                print("Failed to load save file. Unsupported save version.")
                return None

            if algorithm != SaveEncryption.ALGORITHM:
                print("Failed to load save file. Unsupported save algorithm.")
                return None

            if not isinstance(save_data, dict):
                print("Failed to load save file. Save data is invalid.")
                return None

            if not received_hmac:
                print("Failed to load save file. Missing HMAC signature.")
                return None

            if not SaveEncryption._verify_hmac(
                save_data,
                received_hmac,
                secret_key
            ):
                print("Failed to load save file. Save file was modified or corrupted.")
                return None

            return save_data

        except Exception as e:
            print(f"Failed to load save file. Error: {e}")
            return None
