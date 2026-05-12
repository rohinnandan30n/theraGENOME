"""
Flower Federated Learning Client Node Simulator
Simulates hospital/client nodes participating in federated learning
"""

import asyncio
import random
import logging
from datetime import datetime
from typing import Tuple, List, Dict, Optional
import numpy as np

import flwr as fl
from flwr.client import Client, ClientApp
from flwr.common import Context
from flwr.client.message_handler import MessageHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Simulated Model
# ============================================================================

class SimpleNeuralNetwork:
    """
    Simple neural network simulator
    Simulates a pathogen/drug interaction classification model
    """
    
    def __init__(self, node_id: str, model_seed: int = 42):
        self.node_id = node_id
        self.model_seed = model_seed
        random.seed(model_seed)
        np.random.seed(model_seed)
        
        # Simulate model parameters (weights)
        self.weights = np.random.randn(10, 5).astype(np.float32)
        self.bias = np.random.randn(5).astype(np.float32)
        self.loss_history = []
        self.accuracy_history = []
    
    def forward(self, X: np.ndarray) -> np.ndarray:
        """Forward pass"""
        z = np.dot(X, self.weights) + self.bias
        return 1 / (1 + np.exp(-z))  # Sigmoid activation
    
    def train_step(self, X: np.ndarray, y: np.ndarray, lr: float = 0.01) -> Tuple[float, float]:
        """Simulate one training step"""
        # Forward pass
        predictions = self.forward(X)
        
        # Calculate loss (binary crossentropy)
        epsilon = 1e-15
        predictions = np.clip(predictions, epsilon, 1 - epsilon)
        loss = -np.mean(y * np.log(predictions) + (1 - y) * np.log(1 - predictions))
        
        # Simulate gradient descent
        gradients = np.random.randn(*self.weights.shape) * 0.01
        self.weights -= lr * gradients
        self.bias -= lr * np.random.randn(*self.bias.shape) * 0.01
        
        # Calculate accuracy
        predictions_binary = (predictions > 0.5).astype(int)
        accuracy = np.mean(predictions_binary == y)
        
        self.loss_history.append(loss)
        self.accuracy_history.append(accuracy)
        
        return float(loss), float(accuracy)
    
    def get_weights(self) -> np.ndarray:
        """Get model weights as flat array"""
        return np.concatenate([self.weights.flatten(), self.bias.flatten()])
    
    def set_weights(self, weights: np.ndarray) -> None:
        """Set model weights from flat array"""
        weights_size = self.weights.size
        self.weights = weights[:weights_size].reshape(self.weights.shape)
        self.bias = weights[weights_size:]


# ============================================================================
# Flower Client Implementation
# ============================================================================

class FederatedClient(Client):
    """
    Federated Learning Client
    Represents a hospital/clinic participating in training
    """
    
    def __init__(
        self,
        node_id: str,
        hospital_name: str,
        num_samples: int = 100,
        local_epochs: int = 5,
        batch_size: int = 32
    ):
        self.node_id = node_id
        self.hospital_name = hospital_name
        self.num_samples = num_samples
        self.local_epochs = local_epochs
        self.batch_size = batch_size
        
        # Initialize model
        self.model = SimpleNeuralNetwork(node_id)
        
        # Generate synthetic local dataset
        self.X_train, self.y_train = self._generate_local_data()
        self.X_val, self.y_val = self._generate_local_data(0.2)
        
        logger.info(
            f"🏥 Client {node_id} ({hospital_name}) initialized "
            f"with {num_samples} local samples"
        )
    
    def _generate_local_data(self, size_ratio: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic local dataset"""
        num = int(self.num_samples * size_ratio)
        X = np.random.randn(num, 10).astype(np.float32)
        y = (np.random.rand(num) > 0.5).astype(np.float32)
        return X, y
    
    async def fit(self, ins) -> Tuple[List[np.ndarray], int, Dict]:
        """
        Train model on local data
        Part of Flower FedAvg protocol
        """
        logger.info(f"🟢 Client {self.node_id}: Starting local training...")
        
        config = ins.config
        num_epochs = config.get("local_epochs", self.local_epochs)
        
        try:
            total_loss = 0.0
            total_accuracy = 0.0
            
            # Simulate local training for multiple epochs
            for epoch in range(num_epochs):
                loss, accuracy = self.model.train_step(self.X_train, self.y_train)
                total_loss += loss
                total_accuracy += accuracy
                logger.debug(
                    f"  Epoch {epoch + 1}/{num_epochs}: "
                    f"loss={loss:.4f}, acc={accuracy:.4f}"
                )
            
            # Return updated weights
            weights = self.model.get_weights()
            
            logger.info(
                f"✅ Client {self.node_id}: Training complete "
                f"(avg_loss={total_loss/num_epochs:.4f})"
            )
            
            return (
                [weights],  # Updated model weights
                len(self.X_train),  # Number of samples trained
                {"loss": float(total_loss / num_epochs)}
            )
            
        except Exception as e:
            logger.error(f"❌ Client {self.node_id} training error: {e}")
            return ([self.model.get_weights()], len(self.X_train), {"error": str(e)})
    
    async def evaluate(self, ins) -> Tuple[float, int, Dict]:
        """
        Evaluate model on local validation data
        Part of Flower FedAvg protocol
        """
        logger.info(f"📊 Client {self.node_id}: Evaluating...")
        
        try:
            # Set received weights
            if ins.parameters.tensors:
                weights = np.concatenate([np.frombuffer(t, dtype=np.float32) for t in ins.parameters.tensors])
                self.model.set_weights(weights)
            
            # Evaluate
            predictions = self.model.forward(self.X_val)
            predictions_binary = (predictions > 0.5).astype(int)
            accuracy = np.mean(predictions_binary == self.y_val)
            
            loss = np.mean((predictions - self.y_val) ** 2)
            
            logger.info(
                f"✅ Client {self.node_id}: Evaluation complete "
                f"(loss={loss:.4f}, acc={accuracy:.4f})"
            )
            
            return loss, len(self.X_val), {"accuracy": float(accuracy)}
            
        except Exception as e:
            logger.error(f"❌ Client {self.node_id} evaluation error: {e}")
            return 0.0, len(self.X_val), {"error": str(e)}


# ============================================================================
# Client Factory Function
# ============================================================================

def client_fn(context: Context) -> Client:
    """
    Factory function to create client instances
    Called by Flower framework for each client
    """
    
    # Get client ID from Flower context
    node_id = context.state.node_id or "default"
    
    # Map to hospital name
    hospitals = [
        ("node_0", "Boston Medical Center"),
        ("node_1", "Johns Hopkins Hospital"),
        ("node_2", "Mayo Clinic"),
        ("node_3", "Stanford Health"),
        ("node_4", "UCSF Medical Center"),
    ]
    
    hospital_name = next(
        (name for pid, name in hospitals if pid == str(node_id)),
        f"Hospital {node_id}"
    )
    
    # Create and return client
    return FederatedClient(
        node_id=str(node_id),
        hospital_name=hospital_name,
        num_samples=random.randint(50, 200),
        local_epochs=3
    )


# ============================================================================
# Client App Definition
# ============================================================================

app = ClientApp(client_fn=client_fn)


# ============================================================================
# Standalone Client Runner (for testing)
# ============================================================================

async def run_client(
    node_id: str,
    server_address: str = "localhost:8080",
    hospital_name: Optional[str] = None
) -> None:
    """
    Run a single client in standalone mode
    
    Args:
        node_id: Unique client identifier
        server_address: Flower server address
        hospital_name: Hospital/clinic name
    """
    
    if hospital_name is None:
        hospital_name = f"Hospital {node_id}"
    
    logger.info(f"🚀 Starting client {node_id} ({hospital_name})")
    logger.info(f"   Server: {server_address}")
    
    # Create client
    client = FederatedClient(
        node_id=node_id,
        hospital_name=hospital_name,
        num_samples=random.randint(50, 200),
        local_epochs=3
    )
    
    try:
        # Connect to server (this would use Flower's client protocol)
        logger.info(f"✅ Client {node_id} running successfully")
        
        # Simulate some activity
        await asyncio.sleep(60)
        
    except Exception as e:
        logger.error(f"❌ Client error: {e}")
    finally:
        logger.info(f"🛑 Client {node_id} shutting down")


# ============================================================================
# Multi-Client Simulator
# ============================================================================

async def run_multiple_clients(
    num_clients: int = 5,
    server_address: str = "localhost:8080"
) -> None:
    """
    Run multiple clients concurrently
    Simulates a hospital network participating in federated learning
    """
    
    hospitals = [
        "Boston Medical Center",
        "Johns Hopkins Hospital",
        "Mayo Clinic",
        "Stanford Health",
        "UCSF Medical Center",
        "Massachusetts General Hospital",
        "Cleveland Clinic",
        "University of Pennsylvania Medical Center",
    ]
    
    logger.info(f"🏥 Starting {num_clients} federated learning clients...")
    logger.info(f"   Server: {server_address}")
    
    tasks = []
    for i in range(num_clients):
        hospital_name = hospitals[i % len(hospitals)]
        task = run_client(
            node_id=f"node_{i}",
            server_address=server_address,
            hospital_name=hospital_name
        )
        tasks.append(task)
    
    # Run all clients concurrently
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Run specific number of clients
        num_clients = int(sys.argv[1])
        asyncio.run(run_multiple_clients(num_clients=num_clients))
    else:
        # Run 5 clients by default
        asyncio.run(run_multiple_clients(num_clients=5))
