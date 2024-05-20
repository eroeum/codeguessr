"""Application Config"""

class DefaultConfig:
    """Default configuration"""
    API_VERSION = 1.0
    API_TITLE = 'CodeGuessr API'
    OPENAPI_VERSION = '3.0.2'
    OPENAPI_URL_PREFIX = '/'

    OPENAPI_REDOC_PATH = "/redoc"
    OPENAPI_REDOC_URL = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.24.2/"
