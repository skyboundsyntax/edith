"""
Dataset Export Service strictly matching SDD specifications.
Generates structured CSV and JSON exports for download.
"""
import io
import csv
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from backend.app.core.config import settings
from backend.app.db.models import DataRecordModel

class ExportService:
    def __init__(self):
        self.exports_dir = Path(settings.EXPORTS_DIR)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def export_to_json(self, records: List[DataRecordModel], workflow_id: str) -> Dict[str, Any]:
        """
        Converts records to structured JSON and saves to local export directory.
        """
        payload = []
        for r in records:
            data = dict(r.data_json) if isinstance(r.data_json, dict) else {}
            if "work_modality" not in data or not data["work_modality"]:
                rtype = str(data.get("remote_type") or "").lower()
                loc = str(data.get("location") or "").lower()
                is_online = (rtype == "remote") or any(k in loc for k in ["remote", "online", "virtual", "wfh", "anywhere"])
                data["work_modality"] = "Online" if is_online else "Offline"
                if "modality_detail" not in data:
                    data["modality_detail"] = "Online (Remote)" if is_online else ("Offline (Hybrid)" if rtype == "hybrid" else "Offline (On-site)")

            payload.append({
                "record_id": r.id,
                "workflow_id": r.workflow_id,
                "entity_name": r.entity_name,
                "data": data,
                "confidence_score": r.confidence_score,
                "confidence_breakdown": r.confidence_breakdown,
                "human_review_required": r.human_review_required,
                "source_url": r.source_url,
                "source_title": r.source_title,
                "extracted_timestamp": r.extracted_timestamp,
                "raw_snippet": r.raw_snippet
            })

        content_str = json.dumps(payload, indent=2)
        filename = f"export_{workflow_id}_{int(time.time())}.json"
        file_path = self.exports_dir / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_str)

        return {
            "format": "json",
            "filename": filename,
            "record_count": len(records),
            "file_path": str(file_path),
            "download_url": f"/api/export/download?format=json&workflow_id={workflow_id}",
            "raw_content": content_str
        }

    def export_to_csv(self, records: List[DataRecordModel], workflow_id: str) -> Dict[str, Any]:
        """
        Flattens records into tabular CSV format and saves to local export directory.
        """
        if not records:
            content_str = "No records found\n"
            filename = f"export_{workflow_id}_empty.csv"
            file_path = self.exports_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_str)
            return {
                "format": "csv",
                "filename": filename,
                "record_count": 0,
                "file_path": str(file_path),
                "download_url": f"/api/export/download?format=csv&workflow_id={workflow_id}",
                "raw_content": content_str
            }

        # Gather dynamic columns from data_json
        data_keys = set(["work_modality", "modality_detail"])
        for r in records:
            if isinstance(r.data_json, dict):
                data_keys.update(r.data_json.keys())

        standard_columns = ["record_id", "confidence_score", "human_review", "source_url", "timestamp"]
        all_columns = sorted(list(data_keys)) + standard_columns

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=all_columns)
        writer.writeheader()

        for r in records:
            row = {}
            data = dict(r.data_json) if isinstance(r.data_json, dict) else {}
            if "work_modality" not in data or not data["work_modality"]:
                rtype = str(data.get("remote_type") or "").lower()
                loc = str(data.get("location") or "").lower()
                is_online = (rtype == "remote") or any(k in loc for k in ["remote", "online", "virtual", "wfh", "anywhere"])
                data["work_modality"] = "Online" if is_online else "Offline"
                if "modality_detail" not in data:
                    data["modality_detail"] = "Online (Remote)" if is_online else ("Offline (Hybrid)" if rtype == "hybrid" else "Offline (On-site)")

            for k, v in data.items():
                row[k] = ", ".join(str(i) for i in v) if isinstance(v, list) else str(v)

            row["record_id"] = r.id
            row["confidence_score"] = f"{r.confidence_score}%"
            row["human_review"] = "YES" if r.human_review_required else "NO"
            row["source_url"] = r.source_url
            row["timestamp"] = r.extracted_timestamp or ""
            writer.writerow(row)

        content_str = output.getvalue()
        filename = f"export_{workflow_id}_{int(time.time())}.csv"
        file_path = self.exports_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_str)

        return {
            "format": "csv",
            "filename": filename,
            "record_count": len(records),
            "file_path": str(file_path),
            "download_url": f"/api/export/download?format=csv&workflow_id={workflow_id}",
            "raw_content": content_str
        }

export_service = ExportService()
