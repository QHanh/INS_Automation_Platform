import os
import openpyxl

class DetailedPSSEService:
    def __init__(self, file_path, output_path=None):
        self.file_path = file_path
        self.output_path = output_path if output_path else os.path.dirname(file_path)
        self.Vsch = 1
        
    def build_detailed_model(self):
        """Build detailed PSSE model (RAW and SEQ files)"""
        try:
            # Get data from Excel
            from app.classes.psse_classes.detail_model_classes import Get_CLS, RAW_FILE, SEQ_FILE
            
            data = Get_CLS(self.file_path).main()
           
            # Generate RAW file
            raw_filename = os.path.basename(self.file_path).replace(".xlsm", ".raw")
            raw_path = os.path.join(self.output_path, raw_filename)
            raw_generator = RAW_FILE(raw_path, data, self.Vsch)
            raw_generator.main()
            
            # Generate SEQ file
            seq_filename = os.path.basename(self.file_path).replace(".xlsm", ".seq")
            seq_path = os.path.join(self.output_path, seq_filename)
            seq_generator = SEQ_FILE(seq_path, data)
            seq_generator.main()
            
            return {
                "success": True,
                "message": "Detailed model built successfully",
                "raw_file": raw_path,
                "seq_file": seq_path
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error building detailed model: {str(e)}"
            }
