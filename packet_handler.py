import os
import json
import shutil
from typing import Dict, Any

class PacketHandler:
    """
    Manages the creation and update of MOSIP registration packets with OCR data.
    """
    
    def __init__(self, packet_base_path: str):
        self.packet_base_path = packet_base_path
        
    def add_ocr_to_packet(self, packet_id: str, ocr_result: Dict[str, Any]):
        """
        Integrates OCR results into an existing packet structure.
        """
        packet_dir = os.path.join(self.packet_base_path, packet_id)
        if not os.path.exists(packet_dir):
            print(f"Packet directory not found: {packet_dir}")
            return False
            
        try:
            # 1. Save OCR Artifacts
            self._save_artifacts(packet_dir, ocr_result)
            
            # 2. Merge with Demographics (ID JSON)
            self._merge_demographics(packet_dir, ocr_result.get("mosip_data", {}))
            
            print(f"Successfully added OCR data to packet {packet_id}")
            return True
            
        except Exception as e:
            print(f"Error updating packet {packet_id}: {str(e)}")
            return False

    def _save_artifacts(self, packet_dir: str, result: Dict[str, Any]):
        """
        Saves raw OCR data and quality scores as JSON files in the packet.
        """
        # ocr_data.json
        with open(os.path.join(packet_dir, "ocr_data.json"), "w") as f:
            json.dump(result.get("mosip_data", {}), f, indent=2)
            
        # ocr_quality.json
        with open(os.path.join(packet_dir, "ocr_quality.json"), "w") as f:
            json.dump(result.get("quality_scores", {}), f, indent=2)
            
        # ocr_full_text.txt
        full_text = result.get("raw_ocr_data", {}).get("full_text", "") # Assuming full text might be passed
        if full_text:
            with open(os.path.join(packet_dir, "ocr_full_text.txt"), "w") as f:
                f.write(full_text)

    def _merge_demographics(self, packet_dir: str, mosip_data: Dict[str, Any]):
        """
        Merges OCR extracted fields into the main demographic JSON file (ID.json or similar).
        """
        # Identify the demographic JSON file (usually ID.json or demographic.json)
        # We'll look for *.json files and check content or name
        json_files = [f for f in os.listdir(packet_dir) if f.endswith(".json") and "ocr" not in f]
        
        target_file = None
        if "ID.json" in json_files:
            target_file = "ID.json"
        elif "demographic.json" in json_files:
            target_file = "demographic.json"
        elif json_files:
            target_file = json_files[0] # Fallback
            
        if not target_file:
            print("No demographic JSON found to merge.")
            return

        file_path = os.path.join(packet_dir, target_file)
        
        # Read existing
        with open(file_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
                
        # Merge (OCR data does NOT overwrite existing non-empty data by default, 
        # unless we want it to. Usually OCR is pre-fill, so we only fill empty or missing)
        # But for "Integration", maybe we want to update? 
        # Let's assume we update only if missing or if explicitly requested.
        # For this implementation, we will update top-level keys.
        
        # Structure of ID.json varies (simple dict vs identity block).
        # Assuming simple dict for now or "identity" key.
        
        target_dict = data.get("identity", data) # Try to find identity block
        
        for key, value in mosip_data.items():
            if key not in target_dict or not target_dict[key]:
                target_dict[key] = value
                
        # Write back
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

# Example Usage
if __name__ == "__main__":
    # Mock
    handler = PacketHandler("mock_packets")
    os.makedirs("mock_packets/1001", exist_ok=True)
    with open("mock_packets/1001/ID.json", "w") as f:
        json.dump({"identity": {"fullName": "Old Name"}}, f)
        
    ocr_res = {
        "mosip_data": {"fullName": "New Name", "gender": "MLE"},
        "quality_scores": {"blur": 10}
    }
    
    handler.add_ocr_to_packet("1001", ocr_res)
