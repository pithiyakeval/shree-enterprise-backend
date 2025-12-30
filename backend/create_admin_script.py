import asyncio
from app.database import AsyncSessionLocal
from app.crud import create_admin


async def main():
    async with AsyncSessionLocal() as db:
        admin = await create_admin(db, "admin@shree.com", "admin123")
        print("Created admin: ", admin.email, admin.id)


asyncio.run(main())
