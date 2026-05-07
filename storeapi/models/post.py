from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserPostIn(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    body: str


class UserPost(UserPostIn):
    id: int
    user_id: int
    image_url: Optional[str] = None


class UserPostWithLikes(UserPost):
    likes: int


class CommentIn(BaseModel):
    body: str
    post_id: int


class Comment(CommentIn):
    model_config = ConfigDict(
        from_attributes=True
    )  # Now pydantic will try to do return_value[body] if not thenn return_value.body
    id: int
    user_id: int


class UserPostWithComments(BaseModel):
    post: UserPostWithLikes
    comments: list[Comment]


class PostLikeIn(BaseModel):
    post_id: int


class PostLike(PostLikeIn):
    id: int
    user_id: int
