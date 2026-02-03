# llm/__init__.py
# Language model manager module

from .cloud_model_manager import CloudModelManager

# Alias for compatibility
ModelManager = CloudModelManager

__all__ = ['CloudModelManager', 'ModelManager']
