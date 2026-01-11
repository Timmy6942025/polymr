"""
Order signing utilities for Polymarket CLOB.
"""

import logging
from typing import Any, Dict

from ethers import Wallet

logger = logging.getLogger(__name__)


class OrderSigner:
    """Handles order signing for Polymarket CLOB."""

    def __init__(self, private_key: str):
        self.wallet = Wallet(private_key)
        self.address = self.wallet.address

    def sign_order(self, order_data: Dict[str, Any]) -> str:
        """Sign an order with the private key."""
        try:
            message = self._create_order_message(order_data)
            signature = self.wallet.sign_message(message)
            return signature.signature.hex()
        except Exception as e:
            logger.error(f"Order signing failed: {e}")
            raise

    def _create_order_message(self, order_data: Dict[str, Any]) -> str:
        """Create the order message for signing."""
        # Polymarket uses a specific message format for orders
        # The message is the keccak hash of the order data
        import hashlib

        # Sort keys for consistent hashing
        sorted_data = dict(sorted(order_data.items()))
        data_str = str(sorted_data)
        message_hash = hashlib.sha3_256(data_str.encode()).hexdigest()
        return message_hash

    @property
    def public_key(self) -> str:
        """Get the public key address."""
        return self.address


class AuthManager:
    """Manages authentication for Polymarket API."""

    def __init__(self, private_key: str, public_address: str):
        self.signer = OrderSigner(private_key)
        self.public_address = public_address

    async def get_api_credentials(self) -> Dict[str, str]:
        """Get API credentials for the session."""
        return {
            "address": self.public_address,
            "nonce": self._generate_nonce(),
        }

    def _generate_nonce(self) -> str:
        """Generate a nonce for API authentication."""
        import time

        return str(int(time.time() * 1000))
