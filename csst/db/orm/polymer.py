"""Polymer related database models"""
from sqlalchemy import Column, ForeignKey, Integer, Text, Float

from csst.db._base import Base


class Polymer(Base):
    """Model to store polymer id and smiles

    Attributes:
        smiles: smiles string
    """

    __tablename__ = "polymers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    smiles = Column(Text, unique=True)


class LabPolymer(Base):
    """Model to store lab data

    Attributes:
        pol_id (int):
            Polymer id. If None, material is a solvent.
        name (str):
            Name the lab refers to the polymer as.
        number_average_mw_min (float):
            Min number average molecular weight assosicated with the sample
        number_average_mw_max (float):
            Max number average molecular weight assosicated with the sample
        supplier (str):
            Supplier of the sample
    """

    __tablename__ = "lab_polymers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pol_id = Column(Integer, ForeignKey("polymers.id"))
    name = Column(Text, nullable=False, unique=False)
    number_average_mw_min = Column(Float, nullable=True)
    number_average_mw_max = Column(Float, nullable=True)
    supplier = Column(Text, nullable=True)
