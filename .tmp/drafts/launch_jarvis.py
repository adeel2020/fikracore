#!/usr/bin/env python3
"""
JARVIS Launcher - Quick Start Script
Launch JARVIS AI assistant with all superpowers.
"""

import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("jarvis.launcher")


async def main():
    """Main launcher function."""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗                  ║
    ║     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝                  ║
    ║     ██║███████║██████╔╝██║   ██║██║███████╗                  ║
    ║██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║                  ║
    ║╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║                  ║
    ║ ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝                  ║
    ║                                                               ║
    ║     Just A Rather Very Intelligent System                     ║
    ║     v3.0.0 - AgenticAIOPs Platform                           ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        from backend.jarvis.core import JARVIS, JARVISConfig
        
        # Initialize JARVIS
        logger.info("Initializing JARVIS...")
        config = JARVISConfig(
            name="JARVIS",
            version="3.0.0",
            voice_enabled=True,
            vision_enabled=True,
            autopilot_enabled=True,
            security_level="maximum",
            data_residency="UAE",
            neurosol_sync=True,
        )
        
        jarvis = JARVIS(config)
        await jarvis.initialize()
        
        status = jarvis.get_status()
        logger.info(f"JARVIS Status: {status['status']}")
        logger.info(f"Active Powers: {len(status['power_ups_active'])}/8")
        logger.info(f"Data Residency: {status['data_residency']}")
        logger.info(f"NeuroSol Sync: {status['neurosol_sync']}")
        
        print("\n" + "="*60)
        print("JARVIS is ONLINE and ready to assist!")
        print("="*60)
        print("\nAPI Endpoints:")
        print("  - Status:   http://localhost:8000/jarvis/status")
        print("  - Query:    http://localhost:8000/jarvis/query")
        print("  - Stream:   http://localhost:8000/jarvis/stream")
        print("  - UI:       backend/jarvis/ui/jarvis_hud.html")
        print("\n" + "="*60)
        
        # Start FastAPI server
        import uvicorn
        from backend.main import app
        
        logger.info("Starting FastAPI server...")
        server_config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(server_config)
        await server.serve()

        
    except KeyboardInterrupt:
        logger.info("Shutting down JARVIS...")
        await jarvis.shutdown()
        logger.info("JARVIS offline.")
    except Exception as e:
        logger.error(f"Failed to start JARVIS: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
