import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from database import comment_table, database, like_table, post_table
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from models.post import (
    Comment,
    CommentIn,
    PostLike,
    PostLikeIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
    UserPostWithLikes,
)
from models.user import User
from security import get_current_user
from tasks import generate_and_add_to_post

router = APIRouter()

logger = logging.getLogger(__name__)

select_post_and_like = (
    sqlalchemy.select(
        post_table,
        sqlalchemy.func.count(like_table.c.id).label(
            "likes"
        ),  # count function to getthe count of specific table cloumn
    )
    .select_from(post_table.outerjoin(like_table))
    .group_by(post_table.c.id)
)


async def find_post(post_id: int):
    logger.info(f"Finding post with id{post_id}")

    query = post_table.select().where(post_table.c.id == post_id)

    logger.debug(query)

    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
# no need yo import request just to get the current user through depends and pass it as a dependency injection
async def create_post(
    post: UserPostIn,
    current_user: Annotated[User, Depends(get_current_user)],
    background_task: BackgroundTasks,
    request: Request,
    prompt: str = None,
):
    logger.info("creating post")
    # make sure that keys of the dictionary matches keys of database.
    data = {**post.model_dump(), "user_id": current_user.id}  # previously .dict()
    # no need to give id DB will generate it itself
    query = post_table.insert().values(data)
    last_record_id = await database.execute(query)  # we will get back the id

    if prompt:
        background_task.add_task(
            generate_and_add_to_post,
            current_user.email,
            last_record_id,
            request.url_for("get_post_with_comment", post_id=last_record_id),
            database,
            prompt,
        )

    return {**data, "id": last_record_id}


class PostSorting(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"


@router.get("/post", response_model=list[UserPostWithLikes])
async def get_all_posts(sorting: PostSorting = PostSorting.new):
    logger.info("getting all posts")

    if sorting == PostSorting.new:
        query = select_post_and_like.order_by(post_table.c.id.desc())
    elif sorting == PostSorting.old:
        query = select_post_and_like.order_by(post_table.c.id.asc())
    elif sorting == PostSorting.most_likes:
        query = select_post_and_like.order_by(sqlalchemy.desc("likes"))

    logger.debug(query)

    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(
    comment: CommentIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("creating comment")

    post = await find_post(comment.post_id)
    if not post:
        logger.error(f"Post with id {comment.post_id} not found")
        raise HTTPException(status_code=404, detail="Post not found")

    data = {**comment.model_dump(), "user_id": current_user.id}  # previously .dict()
    query = comment_table.insert().values(data)

    logger.debug(query, extra={"email": "bob@example.net"})

    last_comment_id = await database.execute(query)
    return {**data, "id": last_comment_id}


@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    logger.info("getting comment of the post")

    query = comment_table.select().where(comment_table.c.post_id == post_id)

    logger.debug(query)

    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    logger.info("getting post and its comments")

    query = select_post_and_like.where(post_table.c.id == post_id)

    logger.debug(query)

    post = await database.fetch_one(query)

    if not post:
        logger.error(f"Post with id {post_id} not found")
        raise HTTPException(status_code=404, detail="Post not found")

    return {
        "post": post,
        "comments": await get_comments_on_post(post_id),
    }


@router.post("/like", response_model=PostLike, status_code=201)
async def like_post(
    like: PostLikeIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("liking post")

    post = await find_post(like.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    data = {**like.model_dump(), "user_id": current_user.id}
    query = like_table.insert().values(data)

    logger.debug(query)

    last_record_id = await database.execute(query)

    return {
        **data,
        "id": last_record_id,
    }
