import os
import re
import sys
import json
import time
import yaml
import asyncio
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/sft", tags=["sft-pipeline"])

# Base Directory
SFT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sft"))

class SFTConfigUpdate(BaseModel):
    base_model: Optional[str] = None
    learning_rate: Optional[float] = None
    epochs: Optional[int] = None
    batch_size: Optional[int] = None
    micro_batch_size: Optional[int] = None
    gradient_accumulation_steps: Optional[int] = None
    r: Optional[int] = None
    alpha: Optional[int] = None
    max_seq_length: Optional[int] = None

class SFTPipelineManager:
    def __init__(self):
        self.state = "IDLE"  # IDLE, TRAINING, MERGING, COMPLETED, FAILED, EVALUATING
        self.current_method = None
        self.epochs_completed = 0.0
        self.total_epochs = 2.0
        self.current_loss = None
        self.current_grad_norm = None
        self.current_lr = None
        self.elapsed_time_sec = 0
        self.eta_sec = None
        self.logs: List[str] = []
        self.process = None
        self.start_time = None
        self.error_message = None

    def clear(self):
        self.epochs_completed = 0.0
        self.current_loss = None
        self.current_grad_norm = None
        self.current_lr = None
        self.elapsed_time_sec = 0
        self.eta_sec = None
        self.logs = []
        self.error_message = None

    def parse_metrics(self, line: str):
        # Support dict print strings like: {'loss': 3.6355, 'grad_norm': 9.62, 'learning_rate': 0.0001, 'epoch': 0.02}
        try:
            # Check loss
            loss_match = re.search(r"'loss':\s*([0-9\.]+)", line) or re.search(r'"loss":\s*([0-9\.]+)', line)
            if loss_match:
                self.current_loss = float(loss_match.group(1))

            # Check grad norm
            grad_match = re.search(r"'grad_norm':\s*([0-9\.]+)", line) or re.search(r'"grad_norm":\s*([0-9\.]+)', line)
            if grad_match:
                self.current_grad_norm = float(grad_match.group(1))

            # Check learning rate
            lr_match = re.search(r"'learning_rate':\s*([0-9\.-e]+)", line) or re.search(r'"learning_rate":\s*([0-9\.-e]+)', line)
            if lr_match:
                self.current_lr = float(lr_match.group(1))

            # Check epoch
            epoch_match = re.search(r"'epoch':\s*([0-9\.]+)", line) or re.search(r'"epoch":\s*([0-9\.]+)', line)
            if epoch_match:
                self.epochs_completed = float(epoch_match.group(1))

                # Calculate ETA if possible
                if self.epochs_completed > 0 and self.start_time and self.state == "TRAINING":
                    elapsed = time.time() - self.start_time
                    progress_ratio = self.epochs_completed / self.total_epochs
                    total_estimated_time = elapsed / progress_ratio
                    self.eta_sec = max(0, int(total_estimated_time - elapsed))
        except Exception as e:
            print(f"[Log Parser Error] {e}")

    async def run_pipeline_async(self, method: str):
        self.clear()
        self.state = "TRAINING"
        self.current_method = method
        self.start_time = time.time()

        # Load active total epochs from config
        try:
            config_path = os.path.join(SFT_DIR, "train_config.yml")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    cfg = yaml.safe_load(f)
                    self.total_epochs = float(cfg.get("training", {}).get("epochs", 2.0))
        except Exception as e:
            print(f"Warning: Could not read epochs from config: {e}")

        # Choose trainer script
        script_name = "train_corda.py" if method == "corda" else "train_pissa.py"
        cmd = ["uv", "run", "python", script_name]
        if method == "pissa":
            cmd.extend(["--config", "train_config.yml"])

        print(f"Starting SFT training process: {cmd}")
        try:
            # Ensure stdout/stderr is flushed in real-time by setting PYTHONUNBUFFERED
            sub_env = os.environ.copy()
            sub_env["PYTHONUNBUFFERED"] = "1"

            # 1. Start Training Subprocess
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=SFT_DIR,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=sub_env
            )

            # Read stream
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                decoded_line = line.decode("utf-8", errors="replace")
                if '\r' in decoded_line:
                    parts = [p.strip() for p in decoded_line.split('\r') if p.strip()]
                    if parts:
                        decoded_line = parts[-1] + "\n"
                self.logs.append(decoded_line)
                if len(self.logs) > 500:
                    self.logs.pop(0)
                self.parse_metrics(decoded_line)

            exit_code = await self.process.wait()
            if exit_code != 0:
                self.state = "FAILED"
                self.error_message = f"Training failed with exit code {exit_code}"
                return

            # 2. Start Merging Subprocess
            self.state = "MERGING"
            merge_cmd = ["uv", "run", "python", "merge_lora.py"]
            print(f"Starting PEFT weight merging process: {merge_cmd}")

            # Ensure stdout/stderr is flushed in real-time
            sub_env = os.environ.copy()
            sub_env["PYTHONUNBUFFERED"] = "1"

            self.process = await asyncio.create_subprocess_exec(
                *merge_cmd,
                cwd=SFT_DIR,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=sub_env
            )

            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                decoded_line = line.decode("utf-8", errors="replace")
                if '\r' in decoded_line:
                    parts = [p.strip() for p in decoded_line.split('\r') if p.strip()]
                    if parts:
                        decoded_line = parts[-1] + "\n"
                self.logs.append(decoded_line)
                if len(self.logs) > 500:
                    self.logs.pop(0)

            exit_code = await self.process.wait()
            if exit_code != 0:
                self.state = "FAILED"
                self.error_message = f"Weight merging failed with exit code {exit_code}"
                return

            self.state = "COMPLETED"
        except Exception as e:
            self.state = "FAILED"
            self.error_message = f"Pipeline execution failed: {str(e)}"
        finally:
            self.process = None

    async def run_evaluation_async(self):
        self.clear()
        self.state = "EVALUATING"
        self.start_time = time.time()

        cmd = ["uv", "run", "python", "corda_eval.py"]
        print(f"Starting model evaluation process: {cmd}")

        # Ensure stdout/stderr is flushed in real-time
        sub_env = os.environ.copy()
        sub_env["PYTHONUNBUFFERED"] = "1"

        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=SFT_DIR,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=sub_env
            )

            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                decoded_line = line.decode("utf-8", errors="replace")
                if '\r' in decoded_line:
                    parts = [p.strip() for p in decoded_line.split('\r') if p.strip()]
                    if parts:
                        decoded_line = parts[-1] + "\n"
                self.logs.append(decoded_line)
                if len(self.logs) > 500:
                    self.logs.pop(0)

            exit_code = await self.process.wait()
            if exit_code != 0:
                self.state = "FAILED"
                self.error_message = f"Evaluation failed with exit status {exit_code}"
                return

            self.state = "IDLE"
        except Exception as e:
            self.state = "FAILED"
            self.error_message = f"Evaluation execution failed: {str(e)}"
        finally:
            self.process = None


# Global pipeline manager singleton
manager = SFTPipelineManager()


@router.get("/datasets")
async def get_datasets():
    """Scan SFT backend directory for available dataset files."""
    try:
        files = os.listdir(SFT_DIR)
        jsonl_files = [f for f in files if f.endswith(".jsonl")]
        datasets_list = []
        for jf in jsonl_files:
            file_path = os.path.join(SFT_DIR, jf)
            size_kb = round(os.path.getsize(file_path) / 1024, 2)
            
            # Simple line counting for estimation of rows
            row_count = 0
            try:
                with open(file_path, "r", errors="ignore") as f:
                    for _ in f:
                        row_count += 1
            except:
                row_count = 1000  # Default fallback
                
            datasets_list.append({
                "id": jf,
                "name": jf,
                "rows": row_count,
                "size_kb": size_kb
            })
        return datasets_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load datasets: {str(e)}")


@router.get("/config")
async def get_config():
    """Load train_config.yml parameters."""
    config_path = os.path.join(SFT_DIR, "train_config.yml")
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="train_config.yml not found")
    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
            # Flatten or format response for easier frontend usage
            return {
                "base_model": cfg.get("base_model"),
                "merged_dir": cfg.get("merged_dir", "./sft_merged_model"),
                "learning_rate": cfg.get("training", {}).get("learning_rate"),
                "epochs": cfg.get("training", {}).get("epochs"),
                "batch_size": cfg.get("training", {}).get("batch_size"),
                "micro_batch_size": cfg.get("training", {}).get("micro_batch_size"),
                "gradient_accumulation_steps": cfg.get("training", {}).get("gradient_accumulation_steps"),
                "max_seq_length": cfg.get("max_seq_length"),
                "lora": cfg.get("lora", {})
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read train_config.yml: {str(e)}")


@router.post("/config")
async def update_config(update: SFTConfigUpdate):
    """Write updated training configurations back to train_config.yml without removing existing formations."""
    config_path = os.path.join(SFT_DIR, "train_config.yml")
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="train_config.yml not found")
    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)

        # Apply updates gently to keep structure
        if update.base_model is not None:
            cfg["base_model"] = update.base_model
        if update.max_seq_length is not None:
            cfg["max_seq_length"] = update.max_seq_length

        if "training" not in cfg:
            cfg["training"] = {}
        if update.learning_rate is not None:
            cfg["training"]["learning_rate"] = update.learning_rate
        if update.epochs is not None:
            cfg["training"]["epochs"] = update.epochs
        if update.batch_size is not None:
            cfg["training"]["batch_size"] = update.batch_size
        if update.micro_batch_size is not None:
            cfg["training"]["micro_batch_size"] = update.micro_batch_size
        if update.gradient_accumulation_steps is not None:
            cfg["training"]["gradient_accumulation_steps"] = update.gradient_accumulation_steps

        if "lora" not in cfg:
            cfg["lora"] = {}
        if update.r is not None:
            cfg["lora"]["r"] = update.r
        if update.alpha is not None:
            cfg["lora"]["alpha"] = update.alpha

        # Write back to yml
        with open(config_path, "w") as f:
            yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False)

        return {"status": "success", "config": await get_config()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update train_config.yml: {str(e)}")


@router.post("/train")
async def trigger_training(method: str, config_override: Optional[SFTConfigUpdate] = None):
    """Trigger the asynchronous fine-tuning pipeline background task."""
    if method not in ("corda", "pissa"):
        raise HTTPException(status_code=400, detail="Invalid method. Supported: 'corda', 'pissa'")

    if manager.state in ("TRAINING", "MERGING", "EVALUATING"):
        raise HTTPException(status_code=400, detail=f"Pipeline is currently active in state: {manager.state}")

    # Optional config update
    if config_override:
        await update_config(config_override)

    # Spawn background training loop task
    asyncio.create_task(manager.run_pipeline_async(method))
    return {"status": "started", "method": method}


@router.get("/train/status")
async def get_train_status():
    """Stream training status and formatted logs to the frontend."""
    elapsed = 0
    if manager.start_time and manager.state in ("TRAINING", "MERGING", "EVALUATING"):
        elapsed = int(time.time() - manager.start_time)
    elif manager.state == "COMPLETED" or manager.state == "FAILED":
        # Keep static timing if done
        elapsed = manager.elapsed_time_sec or 0
        if not elapsed and manager.start_time:
            elapsed = int(time.time() - manager.start_time)
            manager.elapsed_time_sec = elapsed

    return {
        "state": manager.state,
        "method": manager.current_method,
        "epochs_completed": round(manager.epochs_completed, 3),
        "total_epochs": manager.total_epochs,
        "current_loss": manager.current_loss,
        "current_grad_norm": manager.current_grad_norm,
        "current_lr": manager.current_lr,
        "elapsed_time_sec": elapsed,
        "eta_sec": manager.eta_sec,
        "error_message": manager.error_message,
        "logs": manager.logs[-150:]  # Send last 150 lines
    }


@router.post("/train/stop")
async def stop_training():
    """Terminate the active SFT training or evaluation subprocess."""
    if manager.state == "IDLE":
        raise HTTPException(status_code=400, detail="No active pipeline run to stop.")

    try:
        if manager.process:
            print(f"Terminating SFT subprocess pid={manager.process.pid}...")
            manager.process.terminate()
            await manager.process.wait()

        manager.state = "IDLE"
        manager.logs.append("\n[SYSTEM] Pipeline execution terminated by user.\n")
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to terminate process: {str(e)}")


@router.get("/train/stream")
async def stream_train_status():
    """Stream training status and incremental logs using Server-Sent Events (SSE)."""
    async def log_generator():
        last_log_idx = 0
        # If client connects and training is IDLE but there are old logs, flush them first
        initial_flush = True
        
        while True:
            elapsed = 0
            if manager.start_time and manager.state in ("TRAINING", "MERGING", "EVALUATING"):
                elapsed = int(time.time() - manager.start_time)
            elif manager.state == "COMPLETED" or manager.state == "FAILED":
                elapsed = manager.elapsed_time_sec or 0
                if not elapsed and manager.start_time:
                    elapsed = int(time.time() - manager.start_time)
                    manager.elapsed_time_sec = elapsed

            new_logs = manager.logs[last_log_idx:]
            last_log_idx = len(manager.logs)

            payload = {
                "state": manager.state,
                "method": manager.current_method,
                "epochs_completed": round(manager.epochs_completed, 3),
                "total_epochs": manager.total_epochs,
                "current_loss": manager.current_loss,
                "current_grad_norm": manager.current_grad_norm,
                "current_lr": manager.current_lr,
                "elapsed_time_sec": elapsed,
                "eta_sec": manager.eta_sec,
                "error_message": manager.error_message,
                "new_logs": new_logs
            }
            
            yield f"data: {json.dumps(payload)}\n\n"

            if manager.state in ("IDLE", "COMPLETED", "FAILED"):
                await asyncio.sleep(2.0)
            else:
                await asyncio.sleep(0.8)

    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/evaluate")
async def trigger_evaluation():
    """Trigger model evaluation using corda_eval.py asynchronously."""
    if manager.state in ("TRAINING", "MERGING", "EVALUATING"):
        raise HTTPException(status_code=400, detail=f"Pipeline is currently busy in state: {manager.state}")

    asyncio.create_task(manager.run_evaluation_async())
    return {"status": "evaluation_started"}


@router.get("/evaluate/results")
async def get_evaluation_results():
    """Read evaluation_results.json and serve the metric report."""
    results_path = os.path.join(SFT_DIR, "evaluation_results.json")
    if not os.path.exists(results_path):
        return {
            "status": "not_available",
            "message": "Evaluation results are not ready yet. Please trigger an evaluation run."
        }
    try:
        with open(results_path, "r") as f:
            data = json.load(f)
        return {
            "status": "ready",
            "results": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read evaluation results: {str(e)}")
