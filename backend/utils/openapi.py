#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.routing import APIRoute


def simplify_operation_ids(app: FastAPI) -> None:
    """
    Simplify operation IDs so that the generated client has simpler API function names.

    :param app:
    :return:
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name