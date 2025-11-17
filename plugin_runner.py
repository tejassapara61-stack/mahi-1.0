# Entry point for MAHI 2.0 plugin execution
from core.command_router import route_command

def handle_command(command: str):
    response = route_command(command)
    return response
