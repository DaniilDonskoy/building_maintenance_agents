from ..house_graph.nodes import BaseNode


class BaseRiskEstimation:
    def __init__(self):
        pass
    
    def estimate(self, node: BaseNode) -> float:
        '''
        Gives the "risk of failure" of each node (based on load and vulnerability).
        '''
        return 0.0