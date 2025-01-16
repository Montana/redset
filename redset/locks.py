"""
Locks used to synchronize mutations on queues in Redis.
"""
from dataclasses import dataclass
import time
from typing import Optional, Any

from redset.exceptions import LockTimeout

__all__ = ['Lock']

REDIS_TIME_PRECISION = 0.01

@dataclass
class Lock:
    """
    A distributed lock implementation using Redis SETNX and GETSET.
    
    Implements a context manager pattern for distributed locking. Based on 
    Chris Lamb's implementation.
    
    Example:
        >>> with Lock(redis_client, 'my_lock'):
        ...     print("Critical section")
    
    Attributes:
        redis: Redis client instance
        key: Unique key for the lock
        expires: Time in seconds after which the lock is considered stale (default: 20)
        timeout: Maximum time in seconds to wait for lock acquisition (default: 10)
        poll_interval: Time in seconds between lock acquisition attempts (default: 0.2)
    """
    
    redis: Any  # Type hint is Any since redis client type varies
    key: str
    expires: float = 20.0
    timeout: float = 10.0
    poll_interval: float = 0.2
    
    def __post_init__(self) -> None:
        """Validate initialization parameters."""
        if self.poll_interval < REDIS_TIME_PRECISION:
            raise ValueError(
                f"Poll interval must be >= {REDIS_TIME_PRECISION} due to Redis precision limits"
            )
        if self.expires <= 0:
            raise ValueError("Expires must be positive")
        if self.timeout < 0:
            raise ValueError("Timeout must be non-negative")
    
    def _try_acquire_lock(self, expires: float) -> bool:
        """
        Attempt to acquire the lock.
        
        Args:
            expires: Timestamp when the lock should expire
            
        Returns:
            bool: True if lock was acquired, False otherwise
        """
        # Try to acquire a new lock
        if self.redis.setnx(self.key, expires):
            return True
            
        # Check if existing lock is expired
        current_value = self.redis.get(self.key)
        if not current_value:
            return False
            
        # Account for Redis precision when checking expiration
        adjusted_time = float(current_value) + REDIS_TIME_PRECISION
        if adjusted_time < time.time():
            # Try to replace expired lock
            if self.redis.getset(self.key, expires) == current_value:
                return True
                
        return False
    
    def __enter__(self) -> None:
        """
        Enter the context manager, acquiring the lock.
        
        Raises:
            LockTimeout: If the lock cannot be acquired within the timeout period
        """
        remaining_timeout = self.timeout
        
        while remaining_timeout >= 0:
            expires = time.time() + self.expires
            
            if self._try_acquire_lock(expires):
                return
                
            remaining_timeout -= self.poll_interval
            time.sleep(self.poll_interval)
            
        raise LockTimeout(f"Timeout while waiting for lock '{self.key}'")
    
    def __exit__(self, exc_type: Optional[type], 
                 exc_val: Optional[Exception],
                 exc_tb: Optional[Any]) -> None:
        """Exit the context manager, releasing the lock."""
        self.redis.delete(self.key)
