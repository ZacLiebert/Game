import json
import os

class SaveEncryption:
    """
    Symmetric encryption system using the RC4 stream cipher algorithm.
    Secures game save files to prevent stats and inventory manipulation.
    """

    @staticmethod
    def _ksa(key):
        """
        Key-Scheduling Algorithm (KSA).
        Initializes the permutation in the array "S" based on the provided key.
        """
        key_length = len(key)
        S = list(range(256))
        j = 0
        for i in range(256):
            j = (j + S[i] + key[i % key_length]) % 256
            S[i], S[j] = S[j], S[i]
        return S

    @staticmethod
    def _prga(S, data_length):
        """
        Pseudo-Random Generation Algorithm (PRGA).
        Generates the keystream used for XORing with the data.
        """
        i = 0
        j = 0
        keystream = []
        for _ in range(data_length):
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            K = S[(S[i] + S[j]) % 256]
            keystream.append(K)
        return keystream

    @staticmethod
    def process(data, key_string):
        """
        Encrypts or decrypts the data.
        Since RC4 uses XOR, encryption and decryption are the exact same mathematical operation.
        
        Args:
            data (bytes): The data to encrypt/decrypt.
            key_string (str): The secret key.
            
        Returns:
            bytes: The processed data.
        """
        key = [ord(c) for c in key_string]
        S = SaveEncryption._ksa(key)
        keystream = SaveEncryption._prga(S, len(data))
        
        # XOR the data bytes with the keystream bytes
        res = bytearray()
        for i in range(len(data)):
            res.append(data[i] ^ keystream[i])
        return bytes(res)

    @staticmethod
    def save_game(save_dict, file_path, secret_key="UIT_MUTATION_SECRET"):
        """
        Serializes a Python dictionary to JSON, encrypts it, and writes to a file.
        """
        json_data = json.dumps(save_dict).encode('utf-8')
        encrypted_data = SaveEncryption.process(json_data, secret_key)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)
        return True

    @staticmethod
    def load_game(file_path, secret_key="UIT_MUTATION_SECRET"):
        """
        Reads an encrypted file, decrypts it, and deserializes back to a dictionary.
        """
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
            
        try:
            decrypted_data = SaveEncryption.process(encrypted_data, secret_key)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            print(f"Failed to load save file. It may be corrupted or tampered with. Error: {e}")
            return None