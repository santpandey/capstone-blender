"""
Base Agent class for the multi-agent pipeline
Provides common functionality for all agents
"""

import time
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from .models import AgentResponse, AgentType, AgentStatus

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the pipeline
    Provides common functionality and interface
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        name: str,
        config: Optional[Dict[str, Any]] = None
    ):
        self.agent_type = agent_type
        self.name = name
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.logger = self._setup_logger()
        
        # Performance tracking
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.last_execution_time = 0.0
        
        # Error tracking
        self.error_count = 0
        self.last_error = None
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the agent"""
        logger = logging.getLogger(f"agent.{self.name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    @abstractmethod
    async def process(self, input_data: BaseModel) -> AgentResponse:
        """
        Process input and return response
        Must be implemented by each agent
        """
        pass
    
    async def execute(self, input_data: BaseModel) -> AgentResponse:
        """
        Execute the agent with error handling and performance tracking
        """
        start_time = time.time()
        self.status = AgentStatus.PROCESSING
        
        try:
            self.logger.info(f"Starting execution with input: {type(input_data).__name__}")
            
            # Validate input
            if not self._validate_input(input_data):
                raise ValueError(f"Invalid input for {self.name}")
            
            # Process the request
            response = await self.process(input_data)
            
            # Update performance metrics
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            self.last_execution_time = execution_time
            self.total_execution_time += execution_time
            self.execution_count += 1
            
            # Update response metadata
            response.execution_time_ms = execution_time
            response.agent_type = self.agent_type
            
            if response.success:
                self.status = AgentStatus.COMPLETED
                self.logger.info(f"Execution completed successfully in {execution_time:.2f}ms")
            else:
                self.status = AgentStatus.FAILED
                self.logger.warning(f"Execution failed: {response.message}")
            
            return response
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.status = AgentStatus.FAILED
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"Execution failed after {execution_time:.2f}ms: {e}")
            
            return AgentResponse(
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                success=False,
                message=f"Agent execution failed: {str(e)}",
                execution_time_ms=execution_time,
                errors=[str(e)]
            )
    
    def _validate_input(self, input_data: BaseModel) -> bool:
        """
        Validate input data
        Can be overridden by specific agents
        """
        try:
            # Basic validation - check if it's a valid Pydantic model
            input_data.model_validate(input_data.model_dump())
            return True
        except Exception as e:
            self.logger.error(f"Input validation failed: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health and performance status"""
        avg_execution_time = (
            self.total_execution_time / self.execution_count 
            if self.execution_count > 0 else 0
        )
        
        error_rate = (
            self.error_count / self.execution_count 
            if self.execution_count > 0 else 0
        )
        
        return {
            "agent_name": self.name,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "avg_execution_time_ms": avg_execution_time,
            "last_execution_time_ms": self.last_execution_time,
            "last_error": self.last_error,
            "config": self.config
        }
    
    def reset_metrics(self):
        """Reset performance and error metrics"""
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.last_execution_time = 0.0
        self.error_count = 0
        self.last_error = None
        self.status = AgentStatus.IDLE
        self.logger.info("Metrics reset")
    
    async def health_check(self) -> bool:
        """
        Perform health check
        Can be overridden by specific agents for custom checks
        """
        try:
            # Basic health check - ensure agent can respond
            health_status = self.get_health_status()
            
            # Check error rate
            error_rate = health_status.get("error_rate", 0)
            if error_rate > 0.5:  # More than 50% error rate
                self.logger.warning(f"High error rate detected: {error_rate:.2%}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def __str__(self) -> str:
        return f"{self.name} ({self.agent_type.value})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', type='{self.agent_type.value}', status='{self.status.value}')>"
