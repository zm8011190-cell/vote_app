import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from auth import hash_password, authenticate_user, create_access_token, get_current_user, get_current_active_user, get_db
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from schemas import User, choose, Question as QuestionSchema, QuestionWithImage

import models as models

models.init_db()


def seed_default_questions() -> None:
    db = models.SessionLocal()
    try:
        if db.query(models.Question).count() == 0:
            default_questions = [
                models.Question(question_text="Would you rather travel to the past or the future?", option1="Past", option2="Future"),
                models.Question(question_text="Would you rather have a pet dragon or a pet unicorn?", option1="Dragon", option2="Unicorn"),
                models.Question(question_text="Would you rather live in the mountains or by the beach?", option1="Mountains", option2="Beach"),
                models.Question(question_text="Would you rather always be early or always be late?", option1="Early", option2="Late"),
            ]
            db.add_all(default_questions)
            db.commit()
    finally:
        db.close()


seed_default_questions()

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI()
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.post("/register")
def create_user(user: User, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")

    new_user = models.User(username=user.username, email=user.email, password=hash_password(user.password))

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me")
def read_users_me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}


# the app starts here


questionindex = 0

@app.get("/get_question")
async def get_questions(current_user: models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    global questionindex
    all_questions = db.query(models.Question).all()
    if not all_questions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No questions available")

    current_question = all_questions[questionindex % len(all_questions)]
    questionindex += 1
    current_user.last_question_id = current_question.id
    db.add(current_user)
    db.commit()
    return QuestionSchema(
        id=current_question.id,
        question_text=current_question.question_text,
        option1=current_question.option1,
        option2=current_question.option2)
    


@app.post("/vote")
async def submit_vote(option: choose, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    db_user = current_user

    question_id = getattr(db_user, "last_question_id", None)
    if not question_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No question served — call GET /get_question first")

    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    voted_ids = [v for v in (db_user.voted_questions or "").split(",") if v]
    if str(question.id) in voted_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already voted on this question.")

    if option.choice not in [question.option1, question.option2]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid voting option.")

    db_user.voted_questions = (db_user.voted_questions or "") + f"{question.id},"
    db_user.vote = (db_user.vote or "") + f"{option.choice},"
    db_user.last_question_id = None
    db.add(db_user)
    db.commit()
    return {"message": "Vote recorded successfully."}

# user media enpoints 

@app.post("/add_your_question", response_model=QuestionWithImage)
async def add_question(
    header: str = Form(...),
    question_text: str = Form(...),
    option1: str = Form(...),
    option2: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    file_extension = Path(file.filename).suffix or ".jpg"
    safe_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = UPLOAD_DIR / safe_filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_url = f"/uploads/{safe_filename}"

    new_question = models.User_questions(
        photos=[models.addphoto(imageurl=image_url)],
        header=header,
        question_text=question_text,
        option1=option1,
        option2=option2,
        username=current_user.username,
        question_id=None,
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return {
        "header": new_question.header,
        "question_text": new_question.question_text,
        "option1": new_question.option1,
        "option2": new_question.option2,
        "imageurls": [photo.imageurl for photo in new_question.photos],
    }

@app.get("/media", response_model=list[QuestionWithImage])
def get_media(db: Session = Depends(get_db)):
    media_questions = db.query(models.User_questions).all()
    return [
        {
            "header": question.header,
            "question_text": question.question_text,
            "option1": question.option1,
            "option2": question.option2,
            "imageurls": [photo.imageurl for photo in question.photos],
        }
        for question in media_questions
    ]


@app.get("/media/current", response_model=QuestionWithImage)
def get_current_media_question(db: Session = Depends(get_db)):
    media_question = db.query(models.User_questions).first()
    if not media_question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No media questions available")

    return {
        "header": media_question.header,
        "question_text": media_question.question_text,
        "option1": media_question.option1,
        "option2": media_question.option2,
        "imageurls": [photo.imageurl for photo in media_question.photos],
        "statistics": {
            "total_votes": len(media_question.total_votes) if hasattr(media_question, "total_votes") else 0,
        }
    }


@app.post("/media/vote")
async def vote_on_media(payload: choose, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    question_id = payload.question_id
    if not question_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Media question id is required")

    media_question = db.query(models.User_questions).filter(models.User_questions.header == question_id).first()
    if not media_question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media question not found")

    if payload.choice not in [media_question.option1, media_question.option2]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid voting option.")

    voted_ids = [v for v in (current_user.voted_questions or "").split(",") if v]
    if str(media_question.header) in voted_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already voted on this question.")
    
    vote_count_attr = f"votes_{payload.choice}"
    if not hasattr(media_question, vote_count_attr):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid voting option.")
    
    setattr(media_question, vote_count_attr, getattr(media_question, vote_count_attr, 0) + 1)
    media_question.total_votes = getattr(media_question, "total_votes", 0) + 1
    db.add(media_question)

    current_user.voted_questions = (current_user.voted_questions or "") + f"{media_question.header},"
    current_user.vote = (current_user.vote or "") + f"{payload.choice},"
    db.add(current_user)
    db.commit()
    return {"message": "Vote recorded successfully."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9000)
    






    






