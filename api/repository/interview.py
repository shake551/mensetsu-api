from typing import List

from fastapi import HTTPException
from jose import jwt, JWTError
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from starlette import status

import api.models.interview as interview_model
import api.schemas.interview as interview_schema
import api.schemas.user as user_schema
from api.config.user import SECRET_KEY, ALGORITHM
import api.repository.user as user_repository


def obtain_interview_from_id(interview_id: int, db: Session):
    interview = db.query(interview_model.Interview) \
        .filter(interview_model.Interview.id == interview_id).first()

    if not interview:
        not_found_exception = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find the interview",
        )
        raise not_found_exception

    return interview


def create_interview(
        db: Session,
        interview_create: interview_schema.InterviewCreate,
        token: str,
) -> interview_model.Interview:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = user_schema.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = user_repository.get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception

    interview = interview_model.Interview(**interview_create.dict(), send_by=user.id)

    db.add(interview)
    db.commit()
    db.refresh(interview)

    return interview


def obtain_random_interviews(
        db: Session,
        token: str,
) -> List[interview_schema.Interview]:
    return db.query(interview_model.Interview) \
        .order_by(func.rand()) \
        .limit(5) \
        .all()


def bookmark_interviews(
        bookmark_request: interview_schema.BookmarkInterviewCreate,
        db: Session,
        token: str,
) -> List[interview_schema.Interview]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = user_schema.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = user_repository.get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception

    interview = obtain_interview_from_id(interview_id=bookmark_request.interview_id, db=db)

    bookmark = interview_model.Bookmark(**bookmark_request.dict(), user_id=user.id)

    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)

    return bookmark


def obtain_bookmarked_interviews(
        db: Session,
        token: str,
) -> List[interview_schema.Interview]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = user_schema.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = user_repository.get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception

    return db.query(interview_model.Interview) \
        .join(interview_model.Bookmark,
              and_(interview_model.Bookmark.user_id == user.id,
                   interview_model.Bookmark.interview_id == interview_model.Interview.id)) \
        .order_by(interview_model.Bookmark.created_at) \
        .all()


def delete_bookmark_interview(
        bookmark_request: interview_schema.BookmarkInterviewDelete,
        db: Session,
        token: str,
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = user_schema.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = user_repository.get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception

    interview = obtain_interview_from_id(interview_id=bookmark_request.interview_id, db=db)

    db.query(interview_model.Bookmark) \
        .filter(and_(interview_model.Bookmark.user_id == user.id,
                     interview_model.Bookmark.interview_id == bookmark_request.interview_id)) \
        .delete()
    db.commit()
