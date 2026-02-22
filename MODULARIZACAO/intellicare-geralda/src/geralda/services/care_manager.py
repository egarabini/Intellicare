import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

class CareManager:
    def __init__(self):
        # In-memory storage matching test expectations
        self._plans: Dict[str, Dict] = {}
        self._tasks: Dict[str, Dict] = {}
        self._task_plan: Dict[str, str] = {} # task_id -> plan_id mapping

    def create_plan(self, patient_id: str, conditions: List[str], goals: List[str] = None, patient_name: str = "") -> Dict:
        plan_id = str(uuid.uuid4())
        plan = {
            "id": plan_id,
            "patient_id": patient_id,
            "conditions": conditions,
            "goals": goals or [],
            "patient_name": patient_name,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        self._plans[plan_id] = plan
        return plan

    def get_plan(self, plan_id: str) -> Optional[Dict]:
        return self._plans.get(plan_id)

    def list_plans(self, patient_id: Optional[str] = None) -> List[Dict]:
        if patient_id:
            return [p for p in self._plans.values() if p["patient_id"] == patient_id]
        return list(self._plans.values())

    def add_task(self, plan_id: str, description: str, category: str = "general") -> Dict:
        if plan_id not in self._plans:
            return None
        
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "plan_id": plan_id,
            "description": description,
            "category": category,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self._tasks[task_id] = task
        self._task_plan[task_id] = plan_id
        return task

    def get_tasks(self, plan_id: str, status: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
        tasks = [t for t in self._tasks.values() if t["plan_id"] == plan_id]
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        if category:
            tasks = [t for t in tasks if t["category"] == category]
        return tasks

    def update_task_status(self, task_id: str, status: str, reason: Optional[str] = None) -> Optional[Dict]:
        if task_id not in self._tasks:
            return None
        
        task = self._tasks[task_id]
        task["status"] = status
        task["updated_at"] = datetime.now().isoformat()
        if reason:
            task["status_reason"] = reason
        return task

    def calculate_adherence(self, plan_id: str) -> Dict:
        if plan_id not in self._plans:
            return None
            
        tasks = [t for t in self._tasks.values() if t["plan_id"] == plan_id]
        total = len(tasks)
        if total == 0:
            return {"plan_id": plan_id, "total_tasks": 0, "completed_tasks": 0, "adherence_rate": 0.0}
            
        completed = len([t for t in tasks if t["status"] == "completed"])
        rate = (completed / total) * 100.0
        
        return {
            "plan_id": plan_id,
            "total_tasks": total,
            "completed_tasks": completed,
            "adherence_rate": rate
        }
