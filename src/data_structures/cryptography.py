import hashlib
import hmac
import json
from pathlib import Path


class SaveEncryption:
    """
    Practical save file integrity protection using HMAC-SHA256 only.

    This version does NOT encrypt the save file.
    It stores readable JSON data plus an HMAC signature.

    Benefits:
    - Simple.
    - No external library required.
    - Detects if the save file was modified.
    - More practical than weak custom encryption for this project.

    Limitation:
    - Players can read the save file.
    - Players cannot modify it successfully unless they know the secret key.
    """

    VERSION = 3
    ALGORITHM = "HMAC-SHA256"
    DEFAULT_SECRET_KEY = "UIT_MUTATION_SECRET"

    # ============================================================
    # HMAC HELPERS
    # ============================================================

    @staticmethod
    def _normalize_key(secret_key):
        if isinstance(secret_key, bytes):
            return secret_key

        return str(secret_key).encode("utf-8")

    @staticmethod
    def _serialize_data(data):
        """
        Converts save data into stable JSON bytes.

        Stable serialization is important because HMAC must be calculated
        from the exact same data format every time.
        """
        return json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":")
        ).encode("utf-8")

    @staticmethod
    def _create_hmac(data, secret_key):
        """
        Creates HMAC-SHA256 signature from save data.
        """
        key = SaveEncryption._normalize_key(secret_key)
        message = SaveEncryption._serialize_data(data)

        return hmac.new(
            key,
            message,
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _verify_hmac(data, received_hmac, secret_key):
        """
        Verifies whether the stored HMAC matches the save data.
        """
        expected_hmac = SaveEncryption._create_hmac(data, secret_key)

        return hmac.compare_digest(
            expected_hmac,
            str(received_hmac)
        )

    # ============================================================
    # SAVE / LOAD API
    # ============================================================

    @staticmethod
    def save_game(save_dict, file_path, secret_key=DEFAULT_SECRET_KEY):
        """
        Saves readable JSON data with an HMAC signature.

        Returns:
            True if save succeeded.
            False if save failed.
        """
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
        """
        Loads save data only if the HMAC signature is valid.

        Returns:
            dict if load succeeds.
            None if the file is missing, modified, corrupted, or invalid.
        """
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