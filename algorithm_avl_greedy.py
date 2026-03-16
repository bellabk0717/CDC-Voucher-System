"""
File Name: algorithm_avl_greedy.py

Description: Self-Balancing Tree (AVL) + Greedy Aggregation for merchant reimbursement processing
"""

import os
from typing import List, Dict, Any, Optional, Tuple

import LoadData

# ==================== AVL Tree Implementation ====================
class AVLNode:
    """Node class for AVL Tree"""
    def __init__(self, key: str, data: Any):
        self.key = key
        self.data = data
        self.left: Optional['AVLNode'] = None
        self.right: Optional['AVLNode'] = None
        self.height: int = 1

class AVLTree:
    """
    Self-Balancing AVL Tree for insertion, search, and deletion.
    """
    
    def __init__(self):
        self.root: Optional[AVLNode] = None
    
    def height(self, node: Optional[AVLNode]) -> int:
        """Get height of node"""
        if not node:
            return 0
        return node.height
    
    def balance_factor(self, node: Optional[AVLNode]) -> int:
        """Calculate balance factor of node"""
        if not node:
            return 0
        return self.height(node.left) - self.height(node.right)
    
    def update_height(self, node: AVLNode):
        """Update height of node based on children"""
        node.height = 1 + max(self.height(node.left), self.height(node.right))
    
    def rotate_right(self, z: AVLNode) -> AVLNode:
        """Right rotation for balancing"""
        y = z.left
        T3 = y.right
        
        y.right = z
        z.left = T3
        
        self.update_height(z)
        self.update_height(y)
        
        return y
    
    def rotate_left(self, z: AVLNode) -> AVLNode:
        """Left rotation for balancing"""
        y = z.right
        T2 = y.left
        
        y.left = z
        z.right = T2
        
        self.update_height(z)
        self.update_height(y)
        
        return y
    
    def insert(self, key: str, data: Any = None) -> None:
        """Insert a new node with key and data into AVL tree"""
        self.root = self._insert_recursive(self.root, key, data)
    
    def _insert_recursive(self, node: Optional[AVLNode], key: str, data: Any) -> AVLNode:
        """Recursive insertion with balancing"""
        if not node:
            return AVLNode(key, data)
        
        if key < node.key:
            node.left = self._insert_recursive(node.left, key, data)
        elif key > node.key:
            node.right = self._insert_recursive(node.right, key, data)
        else:
            node.data = data
            return node
        
        self.update_height(node)
        balance = self.balance_factor(node)
        
        # Balance the tree (4 cases)
        if balance > 1 and key < node.left.key:
            return self.rotate_right(node)
        
        if balance < -1 and key > node.right.key:
            return self.rotate_left(node)
        
        if balance > 1 and key > node.left.key:
            node.left = self.rotate_left(node.left)
            return self.rotate_right(node)
        
        if balance < -1 and key < node.right.key:
            node.right = self.rotate_right(node.right)
            return self.rotate_left(node)
        
        return node
    
    def search(self, key: str) -> Optional[AVLNode]:
        """Search for a node by key"""
        return self._search_recursive(self.root, key)
    
    def _search_recursive(self, node: Optional[AVLNode], key: str) -> Optional[AVLNode]:
        """Recursive search"""
        if not node or node.key == key:
            return node
        
        if key < node.key:
            return self._search_recursive(node.left, key)
        else:
            return self._search_recursive(node.right, key)
    
    def inorder_traversal(self) -> List[AVLNode]:
        """In-order traversal to get sorted nodes"""
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node: Optional[AVLNode], result: List[AVLNode]):
        """Recursive in-order traversal"""
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node)
            self._inorder_recursive(node.right, result)


# ==================== Algorithm 1A: Build Merchant AVL Tree ====================

def build_merchant_avl_tree(merchant_list: List[Dict[str, Any]]) -> AVLTree:
    """
    Build AVL Tree for merchant lookup.
    """
    tree = AVLTree()
    
    for merchant in merchant_list:
        merchant_id = merchant['Merchant_ID']
        tree.insert(merchant_id, merchant)
    
    return tree


# ==================== Algorithm 1B: Greedy Aggregation by Merchant ====================

def greedy_aggregate_by_merchant(
    transaction_list: List[Dict[str, Any]],
    merchant_tree: AVLTree,
    bank_swift_lookup: Dict[Tuple[str, str], str]
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Greedy Strategy: Aggregate transactions by merchant (not individual transactions).
    
    Returns:
        Dictionary structure:
        {
            SWIFT_Code: {
                Merchant_ID: {
                    'merchant_id': str,
                    'merchant_info': dict,
                    'total_amount': float,
                    'transaction_ids': list
                }
            }
        }
    """
    # Dictionary to hold merchant aggregates for each bank
    bank_merchants: Dict[str, Dict[str, Dict[str, Any]]] = {}
    
    # Process each transaction
    for record in transaction_list:
        merchant_id = record.get('Merchant_ID')
        amount_redeemed = record.get('Amount_Redeemed_Float', 0.0)
        transaction_id = record.get('Transaction_ID')
        
        # Look up merchant info from AVL tree
        merchant_node = merchant_tree.search(merchant_id)
        if not merchant_node:
            print(f"Warning: Merchant {merchant_id} not found in tree")
            continue
        
        merchant_info = merchant_node.data
        
        # Get SWIFT code
        bank_key = (str(merchant_info['Bank_Code']), str(merchant_info['Branch_Code']))
        swift_code = bank_swift_lookup.get(bank_key, 'UNKNOWN')
        
        # Initialize bank if not exists
        if swift_code not in bank_merchants:
            bank_merchants[swift_code] = {}
        
        # Initialize merchant if not exists
        if merchant_id not in bank_merchants[swift_code]:
            bank_merchants[swift_code][merchant_id] = {
                'merchant_id': merchant_id,
                'merchant_info': merchant_info,
                'total_amount': 0.0,
                'transaction_ids': []
            }
        
        # Aggregate amount for this merchant
        bank_merchants[swift_code][merchant_id]['total_amount'] += amount_redeemed
        bank_merchants[swift_code][merchant_id]['transaction_ids'].append(transaction_id)
    
    return bank_merchants


# ==================== Main Processing Function ====================

def process_reimbursement_avlgreedy_main(
    reimburse_date: str,
    current_run_hour: int,
    run_hour1: int,
    run_hour2: int,
    data_folder: str = ".",
    output_folder: str = "."
) -> List[str]:
    """
    Main processing function for reimbursement.
    
    Returns:
        List of generated reimbursement file names
    """

    # Calculate transaction time range
    start_date, end_date, start_hour, end_hour = LoadData.calculate_transaction_time_range(
        reimburse_date, current_run_hour, run_hour1, run_hour2
    )
    
    # Step 1: Load data
    print("\n[Step 1] Loading data...")
    bank_list = LoadData.load_bankcodes(os.path.join(data_folder, "BankCode.csv"))
    
    # Load merchant JSON instead of CSV
    merchant_list = LoadData.load_merchant_json(os.path.join(data_folder, "merchant_data.json"))
    
    # Load transactions from JSON files
    transaction_list = LoadData.load_transactions_by_time_range(
        start_date, end_date, start_hour, end_hour, data_folder
    )
    
    if bank_list is None or merchant_list is None or transaction_list is None:
        print("Error: Failed to load required data files")
        return []
    
    if not transaction_list:
        print("Warning: No transaction records found in specified time range")
        return []
    
    print(f"  Loaded {len(bank_list)} banks, {len(merchant_list)} merchants, {len(transaction_list)} transactions")
    
    # Build bank SWIFT lookup
    bank_swift_lookup = LoadData.build_bank_swift_lookup(bank_list)
    
    # Step 2: Build merchant AVL tree
    print("[Step 2] Building merchant AVL tree...")
    merchant_tree = build_merchant_avl_tree(merchant_list)
    print(f"  AVL tree built with {len(merchant_list)} merchants")
    
    # Step 3: Greedy aggregation by merchant
    print("[Step 3] Aggregating transactions by merchant...")
    bank_merchants = greedy_aggregate_by_merchant(
        transaction_list, merchant_tree, bank_swift_lookup
    )
    print(f"  Aggregated merchants for {len(bank_merchants)} banks")
    
    # Step 4: Generate reimbursement files
    print("[Step 4] Generating reimbursement CSV files...")
    generated_files = LoadData.write_reimbursement_csv(
        bank_merchants, reimburse_date, current_run_hour, output_folder
    )
    
    # Step 5: Update transaction JSON files with reimburse_id
    print("[Step 5] Updating transaction JSON files with Reimburse_ID...")
    
    # Build merchant_id -> reimburse_id mapping
    merchant_reimburse_ids = {}
    for swift_code, merchants in bank_merchants.items():
        for merchant_id, merchant_data in merchants.items():
            if 'reimburse_id' in merchant_data:
                merchant_reimburse_ids[merchant_id] = merchant_data['reimburse_id']
    
    # Update all transaction files in the time range
    start_dt = LoadData.datetime.strptime(start_date, '%Y%m%d')
    end_dt = LoadData.datetime.strptime(end_date, '%Y%m%d')
    
    current_dt = start_dt
    while current_dt <= end_dt:
        date_str = current_dt.strftime('%Y%m%d')
        for hour in range(24):
            LoadData.update_transaction_json_with_reimburse_id(
                date_str, hour, merchant_reimburse_ids, data_folder
            )
        current_dt += LoadData.timedelta(days=1)
    
    print(f"\n✓ Successfully generated {len(generated_files)} reimbursement files")
    print(f"✓ Updated transaction JSON files with Reimburse_ID")
    print("=" * 60)
    
    return generated_files


# ==================== Testing ====================

if __name__ == "__main__":
    # Configuration
    REIMBURSE_DATE = "20260124"
    DATA_FOLDER = "."
    OUTPUT_FOLDER = "."
    
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    RUN_HOUR1 = 21  # Current run time
    RUN_HOUR2 = 19  # Previous run time
    
    print("=" * 70)
    print(f"Current Run Time: {RUN_HOUR1}:00")
    print(f"Previous Run Time: {RUN_HOUR2}:00")
    print("=" * 70)
    
    generated_files = process_reimbursement_avlgreedy_main(
        reimburse_date=REIMBURSE_DATE,
        current_run_hour=RUN_HOUR1,
        run_hour1=RUN_HOUR1,
        run_hour2=RUN_HOUR2,
        data_folder=DATA_FOLDER,
        output_folder=OUTPUT_FOLDER
    )
    
    print(f"\n✓ Run complete! Generated {len(generated_files)} files")
    print(f"Output files saved to: {OUTPUT_FOLDER}/{REIMBURSE_DATE}/")
