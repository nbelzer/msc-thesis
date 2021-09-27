from .edge_graph import EdgeNode
from .confined_list import ConfinedList

class NodeVisitor:
    current_node: EdgeNode
    node_history: ConfinedList

    def __init__(self):
        self.node_history = ConfinedList()

    def next_nodes(self):
        if len(self.node_history) > 0:
            return self.current_node.neighbours + [ self.node_history.latest_item().identifier ]
        return self.current_node.neighbours

    def set_current_node(self, node: EdgeNode):
        self.node_history.push(self.current_node)
        self.current_node = node
