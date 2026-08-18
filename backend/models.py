from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    soil_records = relationship("SoilData", back_populates="user")
    irrigation_records = relationship("IrrigationData", back_populates="user")


class SoilData(Base):
    __tablename__ = "soil_data"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nitrogen = Column(Float, nullable=False)
    phosphorus = Column(Float, nullable=False)
    potassium = Column(Float, nullable=False)
    ph = Column(Float, nullable=False)
    organic_carbon = Column(Float, nullable=False)
    fertility_score = Column(Float, nullable=False)
    classification = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="soil_records")


class IrrigationData(Base):
    __tablename__ = "irrigation_data"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sm_current = Column(Float, nullable=False)
    sm_optimal = Column(Float, nullable=False)
    smd = Column(Float, nullable=False)
    irrigation_required = Column(Float, nullable=False)
    water_saved = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="irrigation_records")
