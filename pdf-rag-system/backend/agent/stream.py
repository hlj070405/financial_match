"""流式会话管理 - StreamSession / StreamHub"""

import asyncio
import uuid
from collections import deque
from datetime import datetime
from typing import Optional


class StreamSession:
    def __init__(self, stream_id: str, user_id: int, conversation_id: str, max_events: int = 5000):
        self.stream_id = stream_id
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.events = deque(maxlen=max_events)  # [{'id': int, 'chunk': str}]
        self.next_event_id = 1
        self.done = False
        self.updated_at = datetime.utcnow()
        self.condition = asyncio.Condition()

    async def publish_chunk(self, chunk: str):
        async with self.condition:
            self.events.append({
                "id": self.next_event_id,
                "chunk": chunk
            })
            self.next_event_id += 1
            self.updated_at = datetime.utcnow()
            self.condition.notify_all()

    async def close(self):
        async with self.condition:
            self.done = True
            self.updated_at = datetime.utcnow()
            self.condition.notify_all()

    async def stream_from(self, last_event_id: int = 0):
        current_id = max(0, int(last_event_id or 0))

        while True:
            async with self.condition:
                while not self.done and (len(self.events) == 0 or self.events[-1]["id"] <= current_id):
                    await self.condition.wait()

                snapshot = list(self.events)
                is_done = self.done

            pending = [e for e in snapshot if e["id"] > current_id]
            for event in pending:
                current_id = event["id"]
                yield f"id: {event['id']}\n{event['chunk']}"

            if is_done and (len(snapshot) == 0 or current_id >= snapshot[-1]["id"]):
                break


class StreamHub:
    def __init__(self):
        self.sessions = {}  # stream_id -> StreamSession
        self.latest_stream = {}  # (user_id, conversation_id) -> stream_id
        self.keep_seconds = 1800

    def _cleanup(self):
        now = datetime.utcnow()
        expired_keys = []
        for stream_id, session in self.sessions.items():
            age_seconds = (now - session.updated_at).total_seconds()
            if session.done and age_seconds > self.keep_seconds:
                expired_keys.append(stream_id)

        for stream_id in expired_keys:
            session = self.sessions.pop(stream_id, None)
            if not session:
                continue
            key = (session.user_id, session.conversation_id)
            if self.latest_stream.get(key) == stream_id:
                self.latest_stream.pop(key, None)

    def create_session(self, user_id: int, conversation_id: str) -> StreamSession:
        self._cleanup()
        stream_id = str(uuid.uuid4())
        session = StreamSession(
            stream_id=stream_id,
            user_id=user_id,
            conversation_id=conversation_id
        )
        self.sessions[stream_id] = session
        self.latest_stream[(user_id, conversation_id)] = stream_id
        return session

    def get_session(self, user_id: int, conversation_id: str, stream_id: Optional[str] = None) -> Optional[StreamSession]:
        self._cleanup()

        target_stream_id = stream_id or self.latest_stream.get((user_id, conversation_id))
        if not target_stream_id:
            return None

        session = self.sessions.get(target_stream_id)
        if not session:
            return None

        if session.user_id != user_id or session.conversation_id != conversation_id:
            return None

        return session
