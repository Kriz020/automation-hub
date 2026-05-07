from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Automation Hub"
    debug: bool = True
    data_dir: str = "data"
    output_dir: str = "output"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
