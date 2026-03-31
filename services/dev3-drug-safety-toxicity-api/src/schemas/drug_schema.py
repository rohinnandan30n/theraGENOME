"""
SQLAlchemy ORM models for drug safety, pharmacogenomics, and adverse events data.
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Table, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Drug(Base):
    """Represents a drug/compound in the system."""
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    drugbank_id = Column(String(50), unique=True, index=True, nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pgx_recommendations = relationship("PGxRecommendation", back_populates="drug")
    adverse_events = relationship("AdverseEvent", back_populates="drug")
    ddi_interactions_a = relationship(
        "DrugDrugInteraction",
        foreign_keys="DrugDrugInteraction.drug_a_id",
        back_populates="drug_a"
    )
    ddi_interactions_b = relationship(
        "DrugDrugInteraction",
        foreign_keys="DrugDrugInteraction.drug_b_id",
        back_populates="drug_b"
    )


class PGxRecommendation(Base):
    """Pharmacogenomics recommendations linking genes to drugs."""
    __tablename__ = "pgx_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    gene = Column(String(50), index=True, nullable=False)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    recommendation = Column(Text, nullable=False)
    evidence_level = Column(String(50), nullable=True)  # e.g., "1A", "2B", etc.
    phenotype_categories = Column(JSON, nullable=True)
    source = Column(String(100), default="PharmGKB", nullable=True)
    pharmgkb_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    drug = relationship("Drug", back_populates="pgx_recommendations")


class DrugDrugInteraction(Base):
    """Represents drug-drug interactions (DDI) between two drugs."""
    __tablename__ = "drug_drug_interactions"

    id = Column(Integer, primary_key=True, index=True)
    drug_a_id = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    drug_b_id = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    interaction_type = Column(String(100), nullable=True)  # e.g., "inhibition", "induction"
    severity = Column(String(50), nullable=True)  # e.g., "mild", "moderate", "severe"
    description = Column(Text, nullable=True)
    mechanism = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)  # e.g., "DrugBank"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    drug_a = relationship("Drug", foreign_keys=[drug_a_id], back_populates="ddi_interactions_a")
    drug_b = relationship("Drug", foreign_keys=[drug_b_id], back_populates="ddi_interactions_b")


class AdverseEvent(Base):
    """FDA FAERS adverse event reports."""
    __tablename__ = "adverse_events"

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    event_type = Column(String(255), nullable=False)
    event_count = Column(Integer, default=0)
    seriousness_level = Column(String(50), nullable=True)  # e.g., "serious", "non-serious"
    outcomes = Column(JSON, nullable=True)  # e.g., {"hospitalization": 10, "death": 2}
    report_date = Column(DateTime, nullable=True)
    source = Column(String(100), default="FDA-FAERS", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    drug = relationship("Drug", back_populates="adverse_events")
