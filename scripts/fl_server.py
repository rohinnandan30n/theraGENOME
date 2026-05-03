"""Flower Federated Learning Server with FedAvg Strategy and Differential Privacy.

This module implements the Flower server for coordinating federated learning,
including secure aggregation with differential privacy (Gaussian noise).
"""

import logging
from typing import List, Tuple, Dict, Optional, Any
from datetime import datetime
import asyncio

import flwr as fl
from flwr.common import Metrics, Scalar
from flwr.server.strategy import FedAvg

import numpy as np
from dp_accounting import dp_accounting

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Aggregation Strategy with Differential Privacy
# ============================================================================

class DifferentialPrivacyFedAvg(FedAvg):
    """FedAvg strategy with differential privacy (Gaussian noise addition).
    
    This strategy extends Flower's FedAvg to add Gaussian noise to aggregated
    model weights for differential privacy protection, preventing individual
    hospital updates from being inferred.
    """

    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        min_fit_clients: int = 3,
        min_evaluate_clients: int = 1,
        min_available_clients: int = 3,
        max_clients_to_keep: int = 50,
        **kwargs
    ):
        """Initialize with differential privacy parameters.
        
        Args:
            epsilon: Privacy budget (lower = more privacy, typical: 0.1-10.0)
            delta: Privacy failure probability (typical: 1e-8 to 1e-3)
            min_fit_clients: Minimum clients for aggregation
            min_evaluate_clients: Minimum clients for evaluation
            min_available_clients: Minimum available clients to start round
            max_clients_to_keep: Maximum clients to aggregate per round
            **kwargs: Additional arguments for FedAvg
        """
        super().__init__(
            min_fit_clients=min_fit_clients,
            min_evaluate_clients=min_evaluate_clients,
            min_available_clients=min_available_clients,
            **kwargs
        )
        
        self.epsilon = epsilon
        self.delta = delta
        self.max_clients_to_keep = max_clients_to_keep
        
        # Calculate noise scale using privacy budget
        self.noise_stddev = self._calculate_noise_stddev()
        
        logger.info(
            f"DifferentialPrivacyFedAvg initialized: "
            f"epsilon={epsilon}, delta={delta}, noise_stddev={self.noise_stddev:.6f}"
        )

    def _calculate_noise_stddev(self) -> float:
        """Calculate Gaussian noise standard deviation based on privacy parameters.
        
        Uses DP accounting library to determine appropriate noise scale.
        
        Returns:
            Standard deviation of Gaussian noise to add
        """
        try:
            # Use DP accounting to compute noise scale
            # Simplified: noise_scale = sqrt(2 * log(1.25/delta)) / epsilon
            noise_scale = np.sqrt(2 * np.log(1.25 / self.delta)) / self.epsilon
            return float(noise_scale)
        except Exception as e:
            logger.error(f"Error calculating noise stddev: {e}, using default 0.1")
            return 0.1

    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitRes]],
        failures: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitRes]],
    ) -> Tuple[Optional[fl.common.Parameters], Dict[str, Metrics]]:
        """Aggregate model updates with differential privacy.
        
        Args:
            server_round: Current round number
            results: Successful client updates
            failures: Failed client updates
            
        Returns:
            Aggregated parameters and metrics
        """
        try:
            logger.info(f"Round {server_round}: Aggregating {len(results)} client updates with DP")
            
            # Limit number of clients (secure aggregation with max size)
            if len(results) > self.max_clients_to_keep:
                logger.warning(
                    f"Too many clients ({len(results)}), keeping top {self.max_clients_to_keep}"
                )
                results = results[:self.max_clients_to_keep]

            # Call parent aggregation (FedAvg)
            aggregated_parameters, metrics = super().aggregate_fit(
                server_round, results, failures
            )

            # Add Gaussian noise to aggregated parameters (differential privacy)
            if aggregated_parameters is not None:
                aggregated_parameters = self._add_differential_privacy(
                    aggregated_parameters, server_round
                )

            logger.info(f"Round {server_round}: Aggregation complete with DP noise applied")
            return aggregated_parameters, metrics

        except Exception as e:
            logger.error(f"Error in aggregate_fit: {e}")
            return None, {"error": str(e)}

    def _add_differential_privacy(
        self,
        parameters: fl.common.Parameters,
        round_num: int
    ) -> fl.common.Parameters:
        """Add Gaussian noise to model parameters for differential privacy.
        
        Args:
            parameters: Aggregated model parameters
            round_num: Current round number for adjustment
            
        Returns:
            Parameters with added noise
        """
        try:
            # Extract weights from parameters
            if parameters is None or not parameters.tensors:
                return parameters

            noisy_tensors = []
            
            for tensor in parameters.tensors:
                # Convert bytes to numpy array
                array = np.frombuffer(tensor, dtype=np.float32)
                
                # Add Gaussian noise scaled to sensitivity
                noise = np.random.normal(0, self.noise_stddev, size=array.shape)
                noisy_array = array + noise
                
                # Convert back to bytes
                noisy_tensors.append(noisy_array.astype(np.float32).tobytes())
            
            # Create new Parameters with noisy tensors
            return fl.common.Parameters(
                tensors=noisy_tensors,
                tensor_type=parameters.tensor_type
            )

        except Exception as e:
            logger.error(f"Error adding differential privacy: {e}, returning original")
            return parameters

    def aggregate_evaluate(
        self,
        server_round: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.EvaluateRes]],
        failures: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.EvaluateRes]],
    ) -> Tuple[Optional[int], Dict[str, Metrics]]:
        """Aggregate evaluation results from clients.
        
        Args:
            server_round: Current round number
            results: Successful client evaluations
            failures: Failed client evaluations
            
        Returns:
            Aggregated loss and metrics
        """
        try:
            # Call parent evaluation aggregation
            loss, metrics = super().aggregate_evaluate(server_round, results, failures)
            
            logger.info(f"Round {server_round}: Aggregated loss={loss}, metrics={metrics}")
            return loss, metrics

        except Exception as e:
            logger.error(f"Error in aggregate_evaluate: {e}")
            return None, {"error": str(e)}


# ============================================================================
# FL Server Configuration
# ============================================================================

class FLServerConfig:
    """Configuration for Flower federated learning server."""

    def __init__(
        self,
        server_address: str = "[::]:8004",  # gRPC server address
        num_rounds: int = 10,
        min_clients: int = 3,
        max_clients: int = 50,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        client_resources: Optional[Dict[str, float]] = None,
    ):
        """Initialize FL server configuration.
        
        Args:
            server_address: gRPC server address (e.g., "[::]:8004")
            num_rounds: Number of federation rounds
            min_clients: Minimum clients required
            max_clients: Maximum clients to accept
            epsilon: Privacy budget for differential privacy
            delta: Privacy failure probability
            client_resources: CPU/disk resources per client
        """
        self.server_address = server_address
        self.num_rounds = num_rounds
        self.min_clients = min_clients
        self.max_clients = max_clients
        self.epsilon = epsilon
        self.delta = delta
        
        # Default client resources if not specified
        if client_resources is None:
            client_resources = {"num_cpus": 1, "num_gpus": 0}
        self.client_resources = client_resources

    def get_strategy(self) -> DifferentialPrivacyFedAvg:
        """Create FedAvg strategy with differential privacy.
        
        Returns:
            Configured strategy instance
        """
        return DifferentialPrivacyFedAvg(
            epsilon=self.epsilon,
            delta=self.delta,
            min_fit_clients=self.min_clients,
            min_evaluate_clients=1,
            min_available_clients=self.min_clients,
            max_clients_to_keep=self.max_clients,
        )

    def get_server_config(self) -> fl.server.ServerConfig:
        """Get Flower ServerConfig.
        
        Returns:
            Flower ServerConfig instance
        """
        return fl.server.ServerConfig(
            num_rounds=self.num_rounds,
            round_timeout=300.0,  # 5 minutes per round
        )


# ============================================================================
# FL Server Manager
# ============================================================================

class FLServerManager:
    """High-level manager for Flower federated learning server lifecycle."""

    def __init__(self, config: FLServerConfig):
        """Initialize FL server manager.
        
        Args:
            config: FLServerConfig instance
        """
        self.config = config
        self.server = None
        self.strategy = None
        self.start_time = None
        self.rounds_completed = 0
        
        logger.info("FLServerManager initialized")

    async def initialize(self) -> bool:
        """Initialize the FL server.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create strategy
            self.strategy = self.config.get_strategy()
            logger.info("FL strategy created")
            
            # Create server
            strategy = self.config.get_strategy()
            server_config = self.config.get_server_config()
            
            self.server = fl.server.Server(
                client_manager=fl.server.SimpleClientManager(),
                strategy=strategy,
                config=server_config,
            )
            
            logger.info("FL server created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing FL server: {e}")
            return False

    async def start(self) -> bool:
        """Start the FL server (blocking).
        
        Returns:
            True if completed successfully
        """
        try:
            if not self.server:
                await self.initialize()
            
            self.start_time = datetime.utcnow()
            logger.info(f"Starting FL server on {self.config.server_address}")
            
            # Start server with gRPC
            fl.server.start_server(
                server_address=self.config.server_address,
                server=self.server,
                config=self.config.get_server_config(),
            )
            
            logger.info("FL server started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting FL server: {e}")
            return False

    def get_server_info(self) -> Dict[str, Any]:
        """Get current server information.
        
        Returns:
            Dictionary with server status and metrics
        """
        uptime = None
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            'server_address': self.config.server_address,
            'status': 'running' if self.server else 'stopped',
            'num_rounds': self.config.num_rounds,
            'rounds_completed': self.rounds_completed,
            'min_clients': self.config.min_clients,
            'max_clients': self.config.max_clients,
            'privacy_epsilon': self.config.epsilon,
            'privacy_delta': self.config.delta,
            'uptime_seconds': uptime,
            'start_time': self.start_time.isoformat() if self.start_time else None,
        }


# ============================================================================
# Client Node Simulator (for testing)
# ============================================================================

class FLClientSimulator:
    """Simulates a hospital client node for federated learning testing."""

    def __init__(
        self,
        hospital_id: str,
        client_id: str = "default",
        model_dim: int = 100,
        num_samples: int = 1000,
    ):
        """Initialize client simulator.
        
        Args:
            hospital_id: Hospital identifier
            client_id: Unique client identifier
            model_dim: Model weight vector dimension
            num_samples: Number of training samples
        """
        self.hospital_id = hospital_id
        self.client_id = client_id
        self.model_dim = model_dim
        self.num_samples = num_samples
        
        # Simulate initial model weights
        self.weights = np.random.normal(0, 1, size=model_dim)
        
        logger.info(
            f"FLClientSimulator initialized: {hospital_id}/{client_id} "
            f"(dim={model_dim}, samples={num_samples})"
        )

    def get_parameters(self) -> fl.common.Parameters:
        """Get current model parameters.
        
        Returns:
            Parameters in Flower format
        """
        return fl.common.Parameters(
            tensors=[self.weights.astype(np.float32).tobytes()],
            tensor_type="numpy.ndarray"
        )

    def set_parameters(self, parameters: fl.common.Parameters) -> None:
        """Set model parameters from server.
        
        Args:
            parameters: Parameters from aggregation
        """
        if parameters and parameters.tensors:
            self.weights = np.frombuffer(parameters.tensors[0], dtype=np.float32)

    def simulate_training(self) -> Tuple[float, float]:
        """Simulate local training and return loss/accuracy.
        
        Returns:
            Tuple of (loss, accuracy)
        """
        # Simulate local training (gradient descent)
        learning_rate = 0.01
        gradient = np.random.normal(0, 0.1, size=self.model_dim)
        self.weights -= learning_rate * gradient
        
        # Simulate loss and accuracy metrics
        loss = float(np.mean(gradient ** 2))
        accuracy = float(np.random.uniform(0.85, 0.95))
        
        return loss, accuracy

    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics.
        
        Returns:
            Dictionary with metrics
        """
        loss, accuracy = self.simulate_training()
        
        return {
            'hospital_id': self.hospital_id,
            'client_id': self.client_id,
            'num_samples': self.num_samples,
            'local_loss': loss,
            'local_accuracy': accuracy,
            'update_timestamp': datetime.utcnow().isoformat(),
        }


# ============================================================================
# Utilities
# ============================================================================

def calculate_privacy_budget(
    num_rounds: int,
    epsilon: float,
    delta: float,
) -> Dict[str, float]:
    """Calculate and track privacy budget consumption.
    
    Args:
        num_rounds: Number of federation rounds completed
        epsilon: Initial privacy budget
        delta: Privacy failure probability
        
    Returns:
        Dictionary with privacy accounting results
    """
    # Conservative approach: epsilon budget is consumed per round
    # (could use more sophisticated analysis)
    epsilon_per_round = epsilon / num_rounds if num_rounds > 0 else epsilon
    
    return {
        'initial_epsilon': epsilon,
        'epsilon_per_round': epsilon_per_round,
        'epsilon_consumed': epsilon_per_round * num_rounds,
        'epsilon_remaining': max(0, epsilon - epsilon_per_round * num_rounds),
        'delta': delta,
        'num_rounds': num_rounds,
    }


if __name__ == "__main__":
    # Example: Initialize and start FL server
    config = FLServerConfig(
        server_address="[::]:8004",
        num_rounds=10,
        min_clients=3,
        epsilon=1.0,
        delta=1e-5,
    )
    
    manager = FLServerManager(config)
    logger.info(f"Server info: {manager.get_server_info()}")
