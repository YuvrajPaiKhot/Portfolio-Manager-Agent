import json
import os
from typing import List, Dict, Optional

class HoldingsManager:
    
    def __init__(self, filepath: str=r"C:\\Users\\yuvra\\OneDrive\\Desktop\\Portfolio Manager Agent\\Database\\holdings.json"):
        self.filepath = filepath
        self._ensure_file_exists()

        

    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                json.dump([], f)



    def _load(self) -> List[Dict]:
        with open(self.filepath, "r") as f:
            return json.load(f)
        

        
    def _save(self, holding: List[dict]):
        with open(self.filepath, "w") as f:
            json.dump(holding, f, indent=4)



    def add_holding(self, holding: dict) -> str:
        holdings = self._load()
        holdings.append(holding)
        self._save(holdings)

        return "Holdings have been added successfully to demat account"



    def list_holdings(self) -> List[dict]:
        return self._load()
    

    
    def clear_all_holdings(self):
        self._save([])

        return "All holdings have been cleared successfully from demat account"



    def get_holding_by_transaction_id(self, transaction_id: str) -> Optional[dict]:
        holdings = self._load()
        for h in holdings:
            if(h["transaction_id"] == transaction_id):
                return h
        return None
    

    
    def get_holding_by_ticker(self, ticker: str) -> List:
        holdings = self._load()
        return [h for h in holdings if h["ticker"] == ticker]
    

    
    def delete_holding_by_transaction_id(self, transaction_id: str) -> str:
        holdings = self._load()
        new_holdings = []

        for h in holdings:
            if(h["transaction_id"] != transaction_id):
                new_holdings.append(h)

        self._save(new_holdings)

        return f"holding with Transaction ID {transaction_id} deleted successfully"



    def delete_holding_by_ticker(self, ticker: str) -> str:
        holdings = self._load()
        is_deleted = False
        # new_holdings = [h for h in holdings if h["ticker"]!=ticker]
        new_holdings = []

        for h in holdings:
            if(h["ticker"] != ticker):
                new_holdings.append(h)
            else:
                is_deleted = True
        self._save(new_holdings)

        if(is_deleted == False):
            return f"holding with ticker '{ticker}' not found!"
        
        return f"Holdings with ticker '{ticker}' deleted successfully"



    def update_holding(self, transaction_id: str, updated_quantity: int, updated_price: int) -> str:
        holdings = self._load()
        for h in holdings:
            if h["transaction_id"] == transaction_id:
                if(updated_quantity != -1):
                    h["quantity"] = updated_quantity
                if(updated_price != -1):
                    h["price"] = updated_price
                self._save(holdings)
                return f"Holding with Transaction ID {transaction_id} updated successfully"  
        return f"Holding with Transaction ID {transaction_id} could not be updated"
