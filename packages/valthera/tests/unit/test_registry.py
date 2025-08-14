"""Unit tests for the registry system."""

import pytest
from unittest.mock import Mock

from valthera.core.registry import Registry, register_component


class TestRegistry:
    """Test cases for the Registry class."""
    
    def test_init(self):
        """Test registry initialization."""
        registry = Registry()
        
        assert registry._components == {}
        assert registry._defaults == {}
    
    def test_register_component(self):
        """Test component registration."""
        registry = Registry()
        
        # Mock component class
        mock_component = Mock()
        
        # Register component
        registry.register(
            component_type="test_type",
            name="test_component",
            component_class=mock_component,
            config={"param": "value"},
            is_default=True
        )
        
        # Check registration
        assert "test_type" in registry._components
        assert "test_component" in registry._components["test_type"]
        assert registry._components["test_type"]["test_component"]["class"] == mock_component
        assert registry._components["test_type"]["test_component"]["config"] == {"param": "value"}
        assert registry._defaults["test_type"] == "test_component"
    
    def test_register_multiple_components(self):
        """Test registering multiple components of the same type."""
        registry = Registry()
        
        mock_component1 = Mock()
        mock_component2 = Mock()
        
        # Register first component
        registry.register("test_type", "comp1", mock_component1)
        
        # Register second component
        registry.register("test_type", "comp2", mock_component2)
        
        # Check both are registered
        assert len(registry._components["test_type"]) == 2
        assert "comp1" in registry._components["test_type"]
        assert "comp2" in registry._components["test_type"]
    
    def test_get_component(self):
        """Test getting a component."""
        registry = Registry()
        
        mock_component = Mock()
        registry.register("test_type", "test_component", mock_component)
        
        # Get component by name
        result = registry.get("test_type", "test_component")
        assert result == mock_component
    
    def test_get_default_component(self):
        """Test getting default component."""
        registry = Registry()
        
        mock_component = Mock()
        registry.register("test_type", "test_component", mock_component, is_default=True)
        
        # Get default component
        result = registry.get("test_type")  # No name specified
        assert result == mock_component
    
    def test_get_nonexistent_component_type(self):
        """Test getting from nonexistent component type."""
        registry = Registry()
        
        with pytest.raises(KeyError, match="Component type 'nonexistent' not found"):
            registry.get("nonexistent", "component")
    
    def test_get_nonexistent_component(self):
        """Test getting nonexistent component."""
        registry = Registry()
        
        registry.register("test_type", "existing", Mock())
        
        with pytest.raises(KeyError, match="Component 'nonexistent' not found"):
            registry.get("test_type", "nonexistent")
    
    def test_get_without_default(self):
        """Test getting component when no default is set."""
        registry = Registry()
        
        registry.register("test_type", "component", Mock())
        
        with pytest.raises(KeyError, match="No default component"):
            registry.get("test_type")  # No name specified, no default set
    
    def test_get_config(self):
        """Test getting component configuration."""
        registry = Registry()
        
        config = {"param": "value", "other": 123}
        registry.register("test_type", "test_component", Mock(), config=config)
        
        # Get config
        result = registry.get_config("test_type", "test_component")
        assert result == config
    
    def test_get_config_default(self):
        """Test getting default component configuration."""
        registry = Registry()
        
        config = {"param": "value"}
        registry.register("test_type", "test_component", Mock(), config=config, is_default=True)
        
        # Get default config
        result = registry.get_config("test_type")
        assert result == config
    
    def test_list_components(self):
        """Test listing components."""
        registry = Registry()
        
        # Register components
        registry.register("type1", "comp1", Mock())
        registry.register("type1", "comp2", Mock())
        registry.register("type2", "comp3", Mock())
        
        # List all component types
        all_types = registry.list_components()
        assert set(all_types) == {"type1", "type2"}
        
        # List components of specific type
        type1_components = registry.list_components("type1")
        assert set(type1_components) == {"comp1", "comp2"}
        
        # List components of nonexistent type
        nonexistent_components = registry.list_components("nonexistent")
        assert nonexistent_components == []
    
    def test_get_default(self):
        """Test getting default component name."""
        registry = Registry()
        
        # No default set
        assert registry.get_default("test_type") is None
        
        # Set default
        registry.register("test_type", "component", Mock(), is_default=True)
        assert registry.get_default("test_type") == "component"
    
    def test_set_default(self):
        """Test setting default component."""
        registry = Registry()
        
        # Register component
        registry.register("test_type", "component", Mock())
        
        # Set as default
        registry.set_default("test_type", "component")
        assert registry._defaults["test_type"] == "component"
    
    def test_set_default_nonexistent_component(self):
        """Test setting default for nonexistent component."""
        registry = Registry()
        
        with pytest.raises(KeyError, match="Component type 'test_type' not found in registry"):
            registry.set_default("test_type", "nonexistent")
    
    def test_set_default_nonexistent_type(self):
        """Test setting default for nonexistent component type."""
        registry = Registry()
        
        # First register a component type
        registry.register("test_type", "test_component", Mock())
        
        with pytest.raises(KeyError, match="Component 'nonexistent' not found"):
            registry.set_default("test_type", "nonexistent")


class TestRegisterComponentDecorator:
    """Test the register_component decorator."""
    
    def test_register_component_decorator(self):
        """Test the register_component decorator."""
        # Use the global registry instance
        from valthera.core.registry import registry
        
        # Use decorator to register component
        @register_component("test_type", "decorated_component", {"param": "value"}, True)
        class TestComponent:
            pass
        
        # Check registration
        assert "test_type" in registry._components
        assert "decorated_component" in registry._components["test_type"]
        assert registry._components["test_type"]["decorated_component"]["config"] == {"param": "value"}
        assert registry._components["test_type"]["decorated_component"]["name"] == "decorated_component"
        assert registry._defaults["test_type"] == "decorated_component"
        
        # Clean up
        del registry._components["test_type"]
        del registry._defaults["test_type"]
    
    def test_register_component_decorator_no_config(self):
        """Test decorator without config."""
        # Use the global registry instance
        from valthera.core.registry import registry
        
        @register_component("test_type", "no_config_component")
        class TestComponent:
            pass
        
        # Check registration with empty config
        assert registry._components["test_type"]["no_config_component"]["config"] == {}
        assert registry._components["test_type"]["no_config_component"]["name"] == "no_config_component"
        assert "test_type" not in registry._defaults
        
        # Clean up
        del registry._components["test_type"]
    
    def test_register_component_decorator_not_default(self):
        """Test decorator with is_default=False."""
        # Use the global registry instance
        from valthera.core.registry import registry
        
        @register_component("test_type", "not_default_component", is_default=False)
        class TestComponent:
            pass
        
        # Check registration
        assert registry._components["test_type"]["not_default_component"]["name"] == "not_default_component"
        assert "test_type" not in registry._defaults
        
        # Clean up
        del registry._components["test_type"]
