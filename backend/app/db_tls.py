"""TLS configuration shared by runtime, cleanup, and migration connections."""
import ssl


def get_database_ssl_argument(mode: str, root_cert: str | None = None) -> str | ssl.SSLContext:
    """Verify both the server certificate chain and hostname for verify-full."""
    if mode != "verify-full":
        return mode
    context = ssl.create_default_context(cafile=root_cert or None)
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    return context
