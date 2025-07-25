from typing import List, Dict, Any

class Fuser:
    def __init__(self):
        print("Fuser initialized.")

    def fuse(self, results: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Merges results from multiple retrievers.
        
        For now, this is a simple concatenation. In the future, this could involve
        re-ranking, de-duplication, etc.
        """
        print(f"Fusing {len(results)} sets of results...")
        
        fused_results = []
        for res_list in results:
            # Ensure we are extending with a list, even if the retriever had an error
            if isinstance(res_list, list):
                fused_results.extend(res_list)
        
        return fused_results