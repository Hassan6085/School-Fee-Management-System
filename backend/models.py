from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Campus:
    id: int
    name: str

@dataclass
class Class:
    id: int
    name: str
    campus_id: int
    default_fee: int

@dataclass
class Student:
    id: int
    roll: str
    name: str
    father: str
    class_id: int
    campus_id: int
    whatsapp: str
    discount_type: str
    discount_value: int

@dataclass
class Fee:
    id: int
    student_id: int
    year: int
    month: int
    fee_amount: int
    discount: int
    paid: int
    pending: int
    discount_type: str
    note: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class EventFee:
    id: int
    student_id: int
    event_name: str
    amount: int
    paid: int
    pending: int
    created_at: Optional[datetime] = None