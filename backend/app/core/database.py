from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from app.core.config import settings

engine = create_engine(settings.database_url, echo=False)


def init_db():
    SQLModel.metadata.create_all(engine)
    
    # Add missing columns if they don't exist (for existing databases)
    # Use separate transactions for each migration to avoid cascading failures
    
    # 1. Create user table
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS "user" (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_guest BOOLEAN DEFAULT TRUE,
                    email VARCHAR UNIQUE
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_session_id ON \"user\"(session_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_email ON \"user\"(email)"))
    except Exception as e:
        print(f"Note creating user table: {e}")
    
    # 2. Migrate ticker table (add id and user_id columns)
    try:
        with engine.begin() as conn:
            # Check if id column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'ticker' AND column_name = 'id'
            """)).fetchone()
            
            if not result:
                conn.execute(text("ALTER TABLE ticker ADD COLUMN id SERIAL"))
                print("Migrating ticker table to new schema...")
    except Exception as e:
        print(f"Note checking/adding ticker id column: {e}")
    
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE ticker 
                ADD COLUMN IF NOT EXISTS user_id INTEGER
            """))
    except Exception as e:
        print(f"Note adding user_id (may already exist): {e}")
    
    # 3. Create legacy user and assign existing tickers
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO "user" (session_id, is_guest) 
                VALUES ('legacy_user', TRUE)
                ON CONFLICT (session_id) DO NOTHING
            """))
    except Exception as e:
        print(f"Note creating legacy user: {e}")
    
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE ticker 
                SET user_id = (SELECT id FROM "user" WHERE session_id = 'legacy_user')
                WHERE user_id IS NULL
            """))
    except Exception as e:
        print(f"Note assigning legacy user to tickers: {e}")
    
    # 4. Add foreign key constraint
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE ticker 
                DROP CONSTRAINT IF EXISTS fk_ticker_user
            """))
    except Exception as e:
        print(f"Note dropping old constraint: {e}")
    
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE ticker 
                ADD CONSTRAINT fk_ticker_user 
                FOREIGN KEY (user_id) REFERENCES "user"(id)
            """))
    except Exception as e:
        print(f"Note adding foreign key constraint (may already exist): {e}")
    
    # 5. Create unique index
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                DROP INDEX IF EXISTS ix_ticker_user_symbol
            """))
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS ix_ticker_user_symbol 
                ON ticker(user_id, symbol)
            """))
    except Exception as e:
        print(f"Note creating unique index: {e}")
    
    # 6. Add risk_tolerance column
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE ticker 
                ADD COLUMN IF NOT EXISTS risk_tolerance VARCHAR
            """))
    except Exception as e:
        print(f"Note adding risk_tolerance: {e}")
    
    # 7. Add trend column to risksnapshot
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE risksnapshot 
                ADD COLUMN IF NOT EXISTS trend VARCHAR
            """))
    except Exception as e:
        print(f"Note adding trend: {e}")
    
    # 8. Create riskforecast table
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS riskforecast (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR NOT NULL,
                    forecast_date TIMESTAMP NOT NULL,
                    days_ahead INTEGER NOT NULL,
                    predicted_score FLOAT NOT NULL,
                    confidence FLOAT NOT NULL,
                    trend_direction VARCHAR NOT NULL,
                    forecast_reasons TEXT NOT NULL,
                    pattern_match VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
    except Exception as e:
        print(f"Note creating riskforecast table: {e}")
    
    # 9. Create indexes for riskforecast
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_riskforecast_symbol ON riskforecast(symbol)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_riskforecast_forecast_date ON riskforecast(forecast_date)"))
    except Exception as e:
        print(f"Note creating indexes: {e}")


def get_session():
    with Session(engine) as session:
        yield session
