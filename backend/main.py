#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

import uvicorn

from backend.core.registrar import register_app

app = register_app()


if __name__ == '__main__':
    # If you like to DEBUG in the IDE, the main startup method will be very helpful
    # If you prefer to debug using print statements, it is recommended to start the service using the fastapi CLI
    try:
        config = uvicorn.Config(app=f'{Path(__file__).stem}:app', reload=True)
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        raise e