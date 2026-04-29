from app.config import MAX_ACTIVE_PEERS

class PeerManager:
    def __init__(self) -> None:
        self._peers: set = set()

    def can_accept_peer(self) -> bool:
        return len(self._peers) < MAX_ACTIVE_PEERS

    def add(self, peer) -> None:
        self._peers.add(peer)

    def discard(self, peer) -> None:
        self._peers.discard(peer)

    async def close_all(self) -> None:
        peers = list(self._peers)
        self._peers.clear()
        for peer in peers:
            await peer.close()

peer_manager = PeerManager()
