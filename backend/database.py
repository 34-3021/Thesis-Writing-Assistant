from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:bardy575@localhost:3306/test"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True  # echo=True 输出 SQL 调试信息
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()