from .instructions import Instruction, RawInstruction
from . import instructions as instructions
from typing import Iterator
import gzip

class TraceIterator(Iterator):
    """Iterator for a given set of instructions.  Will not when all
    instructions have been returned.
    """
    counter: int
    instructions: list[Instruction]

    def __init__(self, instructions: list[Instruction]):
        self.counter = 0
        self.instructions = instructions

    def __next__(self) -> Instruction:
        if self.counter >= len(self.instructions):
            raise StopIteration()
        instruction = self.instructions[self.counter]
        self.counter += 1
        return instruction

    def reset(self):
        self.counter = 0

    def __len__(self):
        return len(self.instructions)

    @staticmethod
    def from_file(file_path):
        return TraceIterator(InstructionParser.parse_file(file_path))


class InstructionParser:
    """Generic class module that covers different instruction parsing
    methods.
    """
    @staticmethod
    def parse(instruction: str) -> Instruction:
        """Parses an instruction in the form of a sting to a UserInstruction."""
        raw_instruction = RawInstruction(instruction)
        # Instantiate the instruction dynamically using the instruction name.
        return getattr(instructions, f"{raw_instruction.instruction}Instruction")(raw_instruction)

    @staticmethod
    def parse_all(instructions: list[str]) -> list[Instruction]:
        """Parses a set of instructions."""
        return [ InstructionParser.parse(i) for i in instructions ]

    @staticmethod
    def parse_file(file_path) -> list[Instruction]:
        """Reads and parses instructions from file."""
        with gzip.open(file_path, 'rb') as f:
            instructions = InstructionParser.parse_all([ l.decode() for l in f.readlines() ])
        return instructions
