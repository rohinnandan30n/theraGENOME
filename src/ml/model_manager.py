from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pickle
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Manage model versioning and loading"""
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = models_dir
        self.loaded_models = {}
        self.model_metadata = {}
        os.makedirs(models_dir, exist_ok=True)
        logger.info(f"Model registry initialized at {models_dir}")
        self._discover_models()
    
    def _discover_models(self):
        """Auto-discover and register models in the models directory"""
        try:
            if not os.path.exists(self.models_dir):
                return
            
            for filename in os.listdir(self.models_dir):
                if filename.endswith('.pkl'):
                    # Parse filename: model_name_vVERSION.pkl
                    parts = filename.replace('.pkl', '').split('_v')
                    if len(parts) == 2:
                        model_name = parts[0]
                        version = parts[1]
                        model_path = os.path.join(self.models_dir, filename)
                        
                        model_id = f"{model_name}:{version}"
                        if model_id not in self.model_metadata:
                            self.model_metadata[model_id] = {
                                'name': model_name,
                                'version': version,
                                'path': model_path,
                                'registered_at': datetime.utcnow().isoformat(),
                                'model_type': 'sklearn',
                                'description': f'Auto-discovered {model_name} v{version}',
                                'features': [],
                                'performance': {}
                            }
                            logger.info(f"Auto-discovered model: {model_id}")
        except Exception as e:
            logger.error(f"Error discovering models: {str(e)}")
    
    def register_model(self, model_name: str, version: str, model_path: str, 
                       metadata: Dict[str, Any] = None) -> bool:
        """Register a model version"""
        try:
            model_id = f"{model_name}:{version}"
            
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return False
            
            # Store metadata
            if metadata is None:
                metadata = {}
            
            self.model_metadata[model_id] = {
                'name': model_name,
                'version': version,
                'path': model_path,
                'registered_at': datetime.utcnow().isoformat(),
                'model_type': metadata.get('model_type', 'sklearn'),
                'description': metadata.get('description', ''),
                'features': metadata.get('features', []),
                'performance': metadata.get('performance', {})
            }
            
            logger.info(f"Registered model: {model_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error registering model: {str(e)}")
            return False
    
    def load_model(self, model_name: str, version: str = 'latest'):
        """Load model from disk"""
        try:
            # Use latest version if not specified
            if version == 'latest':
                versions = [v for k, v in self.model_metadata.items() if k.startswith(f"{model_name}:")]
                if not versions:
                    raise ValueError(f"No models found for {model_name}")
                # Get latest version (assumes semantic versioning)
                latest_meta = sorted(versions, key=lambda x: x['version'])[-1]
                model_path = latest_meta['path']
            else:
                model_id = f"{model_name}:{version}"
                if model_id not in self.model_metadata:
                    raise ValueError(f"Model not found: {model_id}")
                model_path = self.model_metadata[model_id]['path']
            
            # Check if already loaded
            model_key = f"{model_name}:{version}"
            if model_key in self.loaded_models:
                logger.debug(f"Using cached model: {model_key}")
                return self.loaded_models[model_key]
            
            # Load from disk
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            # Cache model
            self.loaded_models[model_key] = model
            logger.info(f"Loaded model: {model_key}")
            
            return model
        
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def save_model(self, model_name: str, version: str, model, 
                   metadata: Dict[str, Any] = None) -> str:
        """Save model to disk and register"""
        try:
            model_filename = f"{model_name}_v{version}.pkl"
            model_path = os.path.join(self.models_dir, model_filename)
            
            # Save model
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            logger.info(f"Saved model to {model_path}")
            
            # Register model
            self.register_model(model_name, version, model_path, metadata)
            
            return model_path
        
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def get_model_info(self, model_name: str, version: str = 'latest') -> Dict[str, Any]:
        """Get model metadata"""
        try:
            if version == 'latest':
                versions = [v for k, v in self.model_metadata.items() if k.startswith(f"{model_name}:")]
                if not versions:
                    return None
                meta = sorted(versions, key=lambda x: x['version'])[-1]
            else:
                model_id = f"{model_name}:{version}"
                meta = self.model_metadata.get(model_id)
            
            return meta
        
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            return None
    
    def list_models(self, model_name: str = None) -> List[Dict[str, Any]]:
        """List all registered models"""
        if model_name:
            return [v for k, v in self.model_metadata.items() if k.startswith(f"{model_name}:")]
        return list(self.model_metadata.values())


# Global registry
_registry = None


def get_registry(models_dir: str = "./models") -> ModelRegistry:
    """Get or create global model registry"""
    global _registry
    if _registry is None:
        _registry = ModelRegistry(models_dir)
    return _registry
