from datetime import date

from pydantic import BaseModel, Field

from app.models.finance import EntryType
from app.schemas.common import MemberBrief, ORMModel


class EntryCreate(BaseModel):
    type: EntryType
    category: str = Field(min_length=1, max_length=100)
    description: str = ""
    amount: float = Field(gt=0)
    date: date
    event_id: int | None = None


class EntryOut(ORMModel):
    id: int
    type: EntryType
    category: str
    description: str
    amount: float
    date: date
    event_id: int | None
    created_by: MemberBrief


class FinanceSummary(BaseModel):
    total_income: float
    total_expense: float
    balance: float          # reserva da banda: receitas − despesas (partes pagas já descontadas)
    pending_fees: float     # cachês a receber (contratante ainda não pagou)
    pending_payouts: float  # partes dos integrantes ainda não pagas (shows já recebidos)
    pending_costs: float    # custos de show ainda não pagos (shows já recebidos)
