from abc import ABC, abstractmethod

class Serializer(ABC):
    """
    A base class defining the interface for Redis serializers.
    
    This abstract class provides a guideline for implementing serializers 
    for redset. While direct subclassing is not required, implementers should
    match the interface defined here.
    """
    
    @abstractmethod
    def loads(self, str_from_redis: str) -> object:
        """
        Deserialize a string from Redis into a Python object.
        
        Args:
            str_from_redis: The string retrieved from Redis
            
        Returns:
            The deserialized Python object
        
        """
        pass
    
    @abstractmethod
    def dumps(self, obj: object) -> str:
        """
        Serialize a Python object into a string for Redis storage.
        
        Args:
            obj: The Python object to be stored in a sorted set
            
        Returns:
            The serialized string representation
            
        """
        pass
