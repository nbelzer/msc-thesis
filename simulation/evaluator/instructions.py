from dataclasses import dataclass

SYNTAX_MAP = {
    "REQ": "Request",
    "REQUEST": "Request",
    "CON": "Connect",
    "CONNECT": "Connect",
    "DCN": "Disconnect",
    "DISCONNECT": "Disconnect",
    "ITERATION": "SetIteration",
    "REGISTER_NODE": "RegisterNode",
    "GET_STATS": "CollectStatistics",
}

class InstructionError(Exception):
    pass

class UnableToDisconnectError(Exception):
    pass

@dataclass
class RawInstruction:
    instruction: str
    body: list[str]

    def __init__(self, instruction: str):
        parts = instruction.split()
        self.instruction = SYNTAX_MAP[parts[0]]
        self.body = parts[1:]


class Instruction:
    """Generic top-level instruction"""
    pass


class UserInstruction(Instruction):
    user_id: int

    def __init__(self, instruction: RawInstruction):
        self.user_id = instruction.body[0]


class ConnectInstruction(UserInstruction):
    node_id: str

    def __init__(self, instruction: RawInstruction):
        super().__init__(instruction)
        self.node_id = instruction.body[1]

    def __str__(self):
        return f"CONNECT {self.user_id} {self.node_id}"


class DisconnectInstruction(UserInstruction):
    node_id: str

    def __init__(self, instruction: RawInstruction):
        super().__init__(instruction)
        self.node_id = instruction.body[1]

    def __str__(self):
        return f"DISCONNECT {self.user_id} {self.node_id}"


class RequestInstruction(UserInstruction):
    identifier: str
    node_id: str

    def __init__(self, instruction: RawInstruction):
        super().__init__(instruction)
        self.node_id = instruction.body[1]
        self.identifier = instruction.body[2]

    def __str__(self):
        return f"REQUEST {self.user_id} {self.node_id} {self.identifier}"


class SetIterationInstruction(Instruction):
    iteration: int

    def __init__(self, instruction: RawInstruction):
        self.iteration = int(instruction.body[0])

    def __str__(self):
        return f"ITERATION {self.iteration}"


class CollectStatisticsInstruction(Instruction):
    def __init__(self, instruction: RawInstruction):
        pass

    def __str__(self):
        return f"COLLECT_STATS"
