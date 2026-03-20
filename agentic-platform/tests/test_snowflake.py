def test_snowflake_connect_stub():
    from app.services.snowflake_service import SnowflakeService

    svc = SnowflakeService()
    assert isinstance(svc.connect(), dict)
