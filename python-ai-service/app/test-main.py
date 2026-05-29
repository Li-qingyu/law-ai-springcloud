# from fastapi import FastAPI,Path,Query
# from enum import Enum
# from typing import Annotated
# from datetime import datetime
# from decimal import Decimal
# app=FastAPI()
#
# @app.get("/")
# async def read_root():
#     return {"message": "Hello World"}
# @app.get("/add/{a}/{b}")
# async def add(a:int,b:int):
#     return {"result":a+b}
#
# # @app.get("/items/{item_id}")
# # async def read_item(item_id :int =Path(title="物品ID",ge=1,le=1000,description="物品ID必须在1-1000之间")):#ge>=1,le<=1000
# #     return {"item_id":item_id}
#
# class FileExtension(str, Enum):
#     pdf = "pdf"
#     docx = "docx"
#     xlsx = "xlsx"
#
# class ImageFormat(str, Enum):
#     jpg = "jpg"
#     png = "png"
#     gif = "gif"
#
# @app.get("/files/{file_id}/export/{extension}")
# async def export_file(file_id: str, extension: FileExtension):
#     return {"file_id": file_id, "format": extension.value}
#
# @app.get("/images/{image_id}/convert/{format}")
# async def convert_image(image_id: str, format: ImageFormat):
#     return {"image_id": image_id, "output_format": format.value}
#
# fake_items_db = [
#     {"item_name": "Foo"},
#     {"item_name": "Bar"},
#     {"item_name": "Baz"}
# ]
#
# # @app.get("/items/")
# # async def read_item(skip: int = 0, limit: int = 10):
# #     return fake_items_db[skip : skip + limit]
# @app.get("/items/{item_id}")
# async def read_item(
#     item_id: int,
#     short: bool = False
# ):
#     item = {"item_id": item_id}
#     if short:
#         item["short"] = True
#     return item
#
#
# #
# # @app.get("/items/")
# # async def read_items(
# #     min_price: Decimal = 0,
# #     max_price: Decimal = 1000,
# #     created_after: datetime | None = None
# # ):
# #     return {
# #         "min_price": min_price,
# #         "max_price": max_price,
# #         "created_after": created_after
# #     }
#
# @app.get("/users/{user_id}/items/{item_id}")
# async def read_user_item(
#     user_id: int,
#     item_id: str,
#     q: str | None = None,
#     short: bool = False
# ):
#     item = {"item_id": item_id, "owner_id": user_id}
#     if q:
#         item["q"] = q
#     if not short:
#         item["description"] = "This is an amazing item"
#     return item
#
#
#
#
# @app.get("/items/")
# async def read_items(
#     q: Annotated[list[str] | None, Query()] = None
# ):
#     if q:
#         return {"query": q}
#     return {"query": "none"}