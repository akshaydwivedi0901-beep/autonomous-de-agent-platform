from app.services.snowflake_service import SnowflakeService

service = SnowflakeService()

result = service.execute("SELECT CURRENT_VERSION()")

print(result)
