"""Solubility/solvent related database models"""
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Text,
    Float,
)

from csst.db import Base


class Solvent(Base):
    """Solvents used to dissolve polymers

    Attributes:
        smiles (str):
            solvent smiles string
    """

    __tablename__ = "solvents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    smiles = Column(Text, unique=True, nullable=False)


class LabSolvent(Base):
    """Model to store lab sample

    Attributes:
        sol_id: link to solvent table
        name: lab name of the solvent
        percent_purity: Percent purity of the solvent
    """

    __tablename__ = "lab_solvents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sol_id = Column(Integer, ForeignKey("solvents.id"))
    name = Column(Text, nullable=True, unique=False)
    percent_purity = Column(Float, nullable=True)
