"""Benefit IQ Application Entrypoint."""
import uvicorn
from benefit_iq.bootstrap import (
    create_application,
)


app = create_application()


def main() -> None:
    """Run Benefit IQ application using Uvicorn server."""
    uvicorn.run(
        "benefit_iq.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
    )


if __name__ == "__main__":
    main()
