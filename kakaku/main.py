from fastapi import FastAPI, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from routers import (
    users,
    search,
    calcitemcomb,
    admin,
)


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(users.router)
app.include_router(search.router)
app.include_router(calcitemcomb.router)
app.include_router(admin.router)


@app.get("/")
async def root(request: Request):
    return RedirectResponse(
        url=request.url_for("read_users"), status_code=status.HTTP_302_FOUND
    )
