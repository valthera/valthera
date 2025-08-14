"""Component registry system for Valthera."""

from typing import Any, Dict, List, Optional, Type, TypeVar
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Registry:
    """Registry for managing components and their configurations."""
    
    def __init__(self):
        self._components: Dict[str, Dict[str, Any]] = {}
        self._defaults: Dict[str, str] = {}
    
    def register(
        self, 
        component_type: str, 
        name: str, 
        component_class: Type[T], 
        config: Optional[Dict[str, Any]] = None,
        is_default: bool = False
    ) -> None:
        """Register a component.
        
        Args:
            component_type: Type of component (e.g., 'observation_processor', 'action_processor')
            name: Name of the component
            component_class: Class of the component
            config: Default configuration for the component
            is_default: Whether this component should be the default for its type
        """
        if component_type not in self._components:
            self._components[component_type] = {}
        
        self._components[component_type][name] = {
            'class': component_class,
            'config': config or {},
            'name': name
        }
        
        if is_default:
            self._defaults[component_type] = name
        
        logger.info(f"Registered {component_type}: {name}")
    
    def get(self, component_type: str, name: Optional[str] = None) -> Type[T]:
        """Get a component class.
        
        Args:
            component_type: Type of component to get
            name: Name of the component (if None, returns default)
            
        Returns:
            Component class
            
        Raises:
            KeyError: If component type or name not found
        """
        if component_type not in self._components:
            raise KeyError(f"Component type '{component_type}' not found in registry")
        
        if name is None:
            if component_type not in self._defaults:
                raise KeyError(f"No default component for type '{component_type}'")
            name = self._defaults[component_type]
        
        if name not in self._components[component_type]:
            raise KeyError(f"Component '{name}' not found for type '{component_type}'")
        
        return self._components[component_type][name]['class']
    
    def get_config(self, component_type: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Get default configuration for a component.
        
        Args:
            component_type: Type of component
            name: Name of the component (if None, returns default)
            
        Returns:
            Component configuration
        """
        if component_type not in self._components:
            raise KeyError(f"Component type '{component_type}' not found in registry")
        
        if name is None:
            if component_type not in self._defaults:
                raise KeyError(f"No default component for type '{component_type}'")
            name = self._defaults[component_type]
        
        if name not in self._components[component_type]:
            raise KeyError(f"Component '{name}' not found for type '{component_type}'")
        
        return self._components[component_type][name]['config'].copy()
    
    def list_components(self, component_type: Optional[str] = None) -> List[str]:
        """List available components.
        
        Args:
            component_type: If specified, only list components of this type
            
        Returns:
            List of component names
        """
        if component_type is None:
            return list(self._components.keys())
        
        if component_type not in self._components:
            return []
        
        return list(self._components[component_type].keys())
    
    def get_default(self, component_type: str) -> Optional[str]:
        """Get the default component name for a type.
        
        Args:
            component_type: Type of component
            
        Returns:
            Default component name or None
        """
        return self._defaults.get(component_type)
    
    def set_default(self, component_type: str, name: str) -> None:
        """Set the default component for a type.
        
        Args:
            component_type: Type of component
            name: Name of the component to set as default
            
        Raises:
            KeyError: If component not found
        """
        if component_type not in self._components:
            raise KeyError(f"Component type '{component_type}' not found in registry")
        
        if name not in self._components[component_type]:
            raise KeyError(f"Component '{name}' not found for type '{component_type}'")
        
        self._defaults[component_type] = name
        logger.info(f"Set default {component_type}: {name}")


# Global registry instance
registry = Registry()


def register_component(
    component_type: str,
    name: str,
    config: Optional[Dict[str, Any]] = None,
    is_default: bool = False
):
    """Decorator to register a component.
    
    Args:
        component_type: Type of component
        name: Name of the component
        config: Default configuration
        is_default: Whether this should be the default
    """
    def decorator(cls: Type[T]) -> Type[T]:
        registry.register(component_type, name, cls, config, is_default)
        return cls
    return decorator
