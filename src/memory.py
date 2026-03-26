"""
Mem0 integration for long-term memory management
"""
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    logger.warning("Mem0 not available. Install with: pip install mem0ai")


class MemoryManager:
    """Manager for long-term memory using Mem0"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the memory manager.

        Args:
            api_key: Optional Mem0 API key. If not provided, will use local storage.
        """
        self.available = MEM0_AVAILABLE
        if not self.available:
            logger.warning("Mem0 is not available. Memory features will be limited.")
            self.memory = None
            return

        try:
            config = {}
            if api_key:
                config["api_key"] = api_key

            self.memory = Memory(config=config)
            logger.info("Mem0 memory initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Mem0: {e}")
            self.memory = None
            self.available = False

    def add_memory(self, content: str, user_id: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add a memory to the user's long-term memory.

        Args:
            content: The content to remember
            user_id: User identifier
            metadata: Optional metadata about the memory

        Returns:
            True if successful, False otherwise
        """
        if not self.available or not self.memory:
            logger.warning("Mem0 not available, cannot add memory")
            return False

        try:
            self.memory.add(
                content,
                user_id=user_id,
                metadata=metadata or {}
            )
            logger.info(f"Added memory for user {user_id}: {content[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return False

    def search_memory(self, query: str, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant memories.

        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum number of results

        Returns:
            List of relevant memories
        """
        if not self.available or not self.memory:
            logger.warning("Mem0 not available, cannot search memory")
            return []

        try:
            results = self.memory.search(
                query,
                user_id=user_id,
                limit=limit
            )
            logger.info(f"Found {len(results)} memories for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []

    def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all memories for a user.

        Args:
            user_id: User identifier

        Returns:
            List of all memories
        """
        if not self.available or not self.memory:
            logger.warning("Mem0 not available, cannot get memories")
            return []

        try:
            results = self.memory.get_all(user_id=user_id)
            logger.info(f"Retrieved {len(results)} memories for user {user_id}")
            return results
        except Exception as e:
            logger.error(f"Error getting memories: {e}")
            return []

    def update_memory(self, memory_id: str, content: str) -> bool:
        """
        Update an existing memory.

        Args:
            memory_id: Memory identifier
            content: New content

        Returns:
            True if successful, False otherwise
        """
        if not self.available or not self.memory:
            logger.warning("Mem0 not available, cannot update memory")
            return False

        try:
            self.memory.update(memory_id, content)
            logger.info(f"Updated memory {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return False

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: Memory identifier

        Returns:
            True if successful, False otherwise
        """
        if not self.available or not self.memory:
            logger.warning("Mem0 not available, cannot delete memory")
            return False

        try:
            self.memory.delete(memory_id)
            logger.info(f"Deleted memory {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False

    def get_context_for_conversation(self, user_id: str, current_topic: Optional[str] = None) -> str:
        """
        Get relevant context from memory for a conversation.

        Args:
            user_id: User identifier
            current_topic: Optional current topic being discussed

        Returns:
            Context string to include in the agent's prompt
        """
        if not self.available or not self.memory:
            return ""

        try:
            # Get relevant memories
            if current_topic:
                memories = self.search_memory(current_topic, user_id, limit=5)
            else:
                memories = self.get_all_memories(user_id)[-10:]  # Last 10 memories

            if not memories:
                return ""

            # Format memories into context
            context_parts = ["=== Relevant Context from Memory ==="]
            for mem in memories:
                if isinstance(mem, dict):
                    content = mem.get("content", mem.get("text", str(mem)))
                    context_parts.append(f"- {content}")

            context = "\n".join(context_parts)
            return context

        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return ""
