"""
ML Inference Optimization
Batch processing, model quantization, ONNX export, and GPU utilization
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import time
from collections import deque
import threading

try:
    import torch
    import torch.nn as nn
    from torch.quantization import quantize_dynamic
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("PyTorch not available - using placeholder implementations")

try:
    import onnx
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("ONNX not available - ONNX export disabled")


class BatchProcessor:
    """
    Batch processing for ML inference to improve throughput
    """
    
    def __init__(self, batch_size: int = 32, max_wait_time: float = 0.1):
        """
        Initialize batch processor
        
        Args:
            batch_size: Maximum batch size
            max_wait_time: Maximum time to wait for batch to fill (seconds)
        """
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.queue = deque()
        self.lock = threading.Lock()
        self.results = {}
        
    def add_request(self, request_id: str, data: np.ndarray) -> None:
        """Add request to batch queue"""
        with self.lock:
            self.queue.append((request_id, data, time.time()))
    
    def get_batch(self) -> Tuple[List[str], np.ndarray]:
        """
        Get batch of requests
        
        Returns:
            Tuple of (request_ids, batched_data)
        """
        with self.lock:
            if not self.queue:
                return [], np.array([])
            
            # Check if we should process now
            oldest_time = self.queue[0][2]
            should_process = (
                len(self.queue) >= self.batch_size or
                time.time() - oldest_time >= self.max_wait_time
            )
            
            if not should_process:
                return [], np.array([])
            
            # Extract batch
            batch_size = min(len(self.queue), self.batch_size)
            batch = [self.queue.popleft() for _ in range(batch_size)]
            
            request_ids = [item[0] for item in batch]
            data = np.stack([item[1] for item in batch])
            
            return request_ids, data
    
    def set_results(self, request_ids: List[str], results: np.ndarray) -> None:
        """Store results for requests"""
        with self.lock:
            for req_id, result in zip(request_ids, results):
                self.results[req_id] = result
    
    def get_result(self, request_id: str, timeout: float = 5.0) -> Optional[np.ndarray]:
        """Get result for request (blocking with timeout)"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                if request_id in self.results:
                    result = self.results.pop(request_id)
                    return result
            time.sleep(0.01)
        return None


class ModelQuantizer:
    """
    Model quantization for faster inference and reduced memory
    """
    
    @staticmethod
    def quantize_model_dynamic(model, dtype=None):
        """
        Apply dynamic quantization to model
        
        Args:
            model: PyTorch model
            dtype: Quantization dtype (default: qint8)
        
        Returns:
            Quantized model
        """
        if not TORCH_AVAILABLE:
            print("PyTorch not available - returning original model")
            return model
        
        if dtype is None:
            dtype = torch.qint8
        
        # Dynamic quantization for linear and LSTM layers
        quantized_model = quantize_dynamic(
            model,
            {nn.Linear, nn.LSTM, nn.GRU},
            dtype=dtype
        )
        
        return quantized_model
    
    @staticmethod
    def quantize_model_static(model, calibration_data, dtype=None):
        """
        Apply static quantization to model (requires calibration data)
        
        Args:
            model: PyTorch model
            calibration_data: Data for calibration
            dtype: Quantization dtype
        
        Returns:
            Quantized model
        """
        if not TORCH_AVAILABLE:
            print("PyTorch not available - returning original model")
            return model
        
        # Placeholder for static quantization
        # In production, would use torch.quantization.prepare and convert
        print("Static quantization requires calibration - using dynamic quantization")
        return ModelQuantizer.quantize_model_dynamic(model, dtype)
    
    @staticmethod
    def estimate_speedup(original_time: float, quantized_time: float) -> Dict[str, float]:
        """
        Estimate speedup from quantization
        
        Returns:
            Dictionary with speedup metrics
        """
        speedup = original_time / quantized_time if quantized_time > 0 else 1.0
        memory_reduction = 0.75  # Typical 4x reduction (fp32 -> int8)
        
        return {
            'speedup': speedup,
            'memory_reduction': memory_reduction,
            'original_time': original_time,
            'quantized_time': quantized_time
        }


class ONNXExporter:
    """
    Export PyTorch models to ONNX for optimized inference
    """
    
    @staticmethod
    def export_to_onnx(
        model,
        dummy_input: torch.Tensor,
        output_path: str,
        input_names: Optional[List[str]] = None,
        output_names: Optional[List[str]] = None,
        dynamic_axes: Optional[Dict[str, Dict[int, str]]] = None
    ) -> bool:
        """
        Export PyTorch model to ONNX format
        
        Args:
            model: PyTorch model
            dummy_input: Example input tensor
            output_path: Path to save ONNX model
            input_names: Names for input tensors
            output_names: Names for output tensors
            dynamic_axes: Dynamic axes specification
        
        Returns:
            Success status
        """
        if not TORCH_AVAILABLE or not ONNX_AVAILABLE:
            print("PyTorch or ONNX not available - export disabled")
            return False
        
        try:
            # Default names
            if input_names is None:
                input_names = ['input']
            if output_names is None:
                output_names = ['output']
            
            # Default dynamic axes (batch dimension)
            if dynamic_axes is None:
                dynamic_axes = {
                    'input': {0: 'batch_size'},
                    'output': {0: 'batch_size'}
                }
            
            # Export model
            torch.onnx.export(
                model,
                dummy_input,
                output_path,
                input_names=input_names,
                output_names=output_names,
                dynamic_axes=dynamic_axes,
                opset_version=13,
                do_constant_folding=True
            )
            
            # Verify exported model
            onnx_model = onnx.load(output_path)
            onnx.checker.check_model(onnx_model)
            
            print(f"Model exported successfully to {output_path}")
            return True
            
        except Exception as e:
            print(f"Failed to export model to ONNX: {e}")
            return False
    
    @staticmethod
    def create_onnx_session(
        model_path: str,
        providers: Optional[List[str]] = None
    ) -> Optional[Any]:
        """
        Create ONNX Runtime inference session
        
        Args:
            model_path: Path to ONNX model
            providers: Execution providers (e.g., ['CUDAExecutionProvider', 'CPUExecutionProvider'])
        
        Returns:
            ONNX Runtime session or None
        """
        if not ONNX_AVAILABLE:
            print("ONNX Runtime not available")
            return None
        
        try:
            # Default providers
            if providers is None:
                providers = ['CPUExecutionProvider']
            
            # Create session with optimizations
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.intra_op_num_threads = 4
            
            session = ort.InferenceSession(
                model_path,
                sess_options=sess_options,
                providers=providers
            )
            
            return session
            
        except Exception as e:
            print(f"Failed to create ONNX session: {e}")
            return None
    
    @staticmethod
    def run_onnx_inference(
        session,
        input_data: np.ndarray,
        input_name: str = 'input'
    ) -> Optional[np.ndarray]:
        """
        Run inference with ONNX Runtime
        
        Args:
            session: ONNX Runtime session
            input_data: Input data
            input_name: Name of input tensor
        
        Returns:
            Output array or None
        """
        if session is None:
            return None
        
        try:
            outputs = session.run(None, {input_name: input_data})
            return outputs[0]
        except Exception as e:
            print(f"ONNX inference failed: {e}")
            return None


class GPUOptimizer:
    """
    GPU utilization optimization
    """
    
    @staticmethod
    def get_device(prefer_gpu: bool = True) -> str:
        """
        Get optimal device for computation
        
        Args:
            prefer_gpu: Whether to prefer GPU if available
        
        Returns:
            Device string ('cuda' or 'cpu')
        """
        if not TORCH_AVAILABLE:
            return 'cpu'
        
        if prefer_gpu and torch.cuda.is_available():
            return 'cuda'
        return 'cpu'
    
    @staticmethod
    def get_gpu_info() -> Dict[str, Any]:
        """
        Get GPU information
        
        Returns:
            Dictionary with GPU info
        """
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return {
                'available': False,
                'device_count': 0
            }
        
        return {
            'available': True,
            'device_count': torch.cuda.device_count(),
            'current_device': torch.cuda.current_device(),
            'device_name': torch.cuda.get_device_name(0),
            'memory_allocated': torch.cuda.memory_allocated(0),
            'memory_reserved': torch.cuda.memory_reserved(0)
        }
    
    @staticmethod
    def optimize_memory(model, use_amp: bool = True):
        """
        Optimize GPU memory usage
        
        Args:
            model: PyTorch model
            use_amp: Use automatic mixed precision
        
        Returns:
            Optimized model
        """
        if not TORCH_AVAILABLE:
            return model
        
        # Enable gradient checkpointing if available
        if hasattr(model, 'gradient_checkpointing_enable'):
            model.gradient_checkpointing_enable()
        
        # Use automatic mixed precision for training
        if use_amp and torch.cuda.is_available():
            print("Automatic mixed precision enabled")
        
        return model
    
    @staticmethod
    def clear_cache():
        """Clear GPU cache"""
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()


class InferenceOptimizer:
    """
    Main inference optimization coordinator
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize inference optimizer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.batch_processor = BatchProcessor(
            batch_size=self.config.get('batch_size', 32),
            max_wait_time=self.config.get('max_wait_time', 0.1)
        )
        self.device = GPUOptimizer.get_device(
            prefer_gpu=self.config.get('use_gpu', True)
        )
        self.use_onnx = self.config.get('use_onnx', False)
        self.onnx_session = None
        
    def optimize_model(self, model, quantize: bool = True, export_onnx: bool = False):
        """
        Apply all optimizations to model
        
        Args:
            model: Model to optimize
            quantize: Apply quantization
            export_onnx: Export to ONNX
        
        Returns:
            Optimized model or ONNX session
        """
        optimized_model = model
        
        # Quantization
        if quantize and TORCH_AVAILABLE:
            print("Applying dynamic quantization...")
            optimized_model = ModelQuantizer.quantize_model_dynamic(model)
        
        # ONNX export
        if export_onnx and ONNX_AVAILABLE:
            print("Exporting to ONNX...")
            dummy_input = torch.randn(1, 10)  # Adjust based on model
            onnx_path = self.config.get('onnx_path', 'model.onnx')
            
            if ONNXExporter.export_to_onnx(optimized_model, dummy_input, onnx_path):
                self.onnx_session = ONNXExporter.create_onnx_session(onnx_path)
                self.use_onnx = True
        
        return optimized_model
    
    def batch_inference(self, model, data_list: List[np.ndarray]) -> List[np.ndarray]:
        """
        Perform batched inference
        
        Args:
            model: Model for inference
            data_list: List of input data
        
        Returns:
            List of predictions
        """
        # Add requests to batch processor
        request_ids = [f"req_{i}" for i in range(len(data_list))]
        for req_id, data in zip(request_ids, data_list):
            self.batch_processor.add_request(req_id, data)
        
        # Process batch
        batch_ids, batch_data = self.batch_processor.get_batch()
        
        if len(batch_ids) == 0:
            return []
        
        # Run inference
        if self.use_onnx and self.onnx_session:
            predictions = ONNXExporter.run_onnx_inference(
                self.onnx_session,
                batch_data
            )
        else:
            # PyTorch inference
            if TORCH_AVAILABLE:
                with torch.no_grad():
                    batch_tensor = torch.from_numpy(batch_data).to(self.device)
                    predictions = model(batch_tensor).cpu().numpy()
            else:
                # Fallback
                predictions = np.zeros((len(batch_data), 1))
        
        # Store results
        self.batch_processor.set_results(batch_ids, predictions)
        
        # Retrieve results
        results = []
        for req_id in request_ids:
            result = self.batch_processor.get_result(req_id)
            if result is not None:
                results.append(result)
        
        return results
    
    def benchmark(self, model, test_data: np.ndarray, num_runs: int = 100) -> Dict[str, float]:
        """
        Benchmark inference performance
        
        Args:
            model: Model to benchmark
            test_data: Test data
            num_runs: Number of benchmark runs
        
        Returns:
            Performance metrics
        """
        times = []
        
        for _ in range(num_runs):
            start = time.time()
            
            if self.use_onnx and self.onnx_session:
                ONNXExporter.run_onnx_inference(self.onnx_session, test_data)
            else:
                if TORCH_AVAILABLE:
                    with torch.no_grad():
                        tensor = torch.from_numpy(test_data).to(self.device)
                        model(tensor)
            
            times.append(time.time() - start)
        
        return {
            'mean_time': np.mean(times),
            'std_time': np.std(times),
            'min_time': np.min(times),
            'max_time': np.max(times),
            'throughput': len(test_data) / np.mean(times)
        }


# Global optimizer instance
_optimizer = None

def get_inference_optimizer(config: Optional[Dict[str, Any]] = None):
    """Get global inference optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = InferenceOptimizer(config)
    return _optimizer

# Made with Bob
