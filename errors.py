class InstallerError(Exception):
    """Base error for jackson_installer."""


class CheckoutError(InstallerError):
    pass


class BuildSystemError(InstallerError):
    pass


class InstrumentationError(InstallerError):
    pass


class DownloadError(InstallerError):
    pass


