import os
import openai
import wget
import pathlib
import pdfplumber
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseSettings, BaseModel


class Settings(BaseSettings):
    openai.api_type = "azure"
    openai.api_base = os.getenv("OPENAI_API_BASE")
    openai.api_version = "2022-06-01-preview"
    openai.api_key = os.getenv("OPENAI_API_KEY")


settings = Settings()
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Payload(BaseModel):
    paper_url: str


async def get_paper(paper_url):
    """
    Downloads a paper from url and returns
    the local path to that file.
    """
    downloaded_paper = wget.download(paper_url)
    downloaded_paper_file_path = pathlib.Path(downloaded_paper)

    return downloaded_paper_file_path


async def generate_tldr(content):
    tldr_tag = "\n tl;dr:"

    for page in content:
        text = page.extract_text() + tldr_tag
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=text,
            temperature=0.8,
            max_tokens=140,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n"]
        )
        print(f'GPT output: {response}')
        return response["choices"][0]["text"]


@app.get("/health")
async def health():
    return {"status": "Ok"}


# Generate a tldr for a pdf paper
@app.post("/tldr")
async def tldr(req: Payload):
    if not req.paper_url:
        print("No paper url provided")
        return {"error": "No paper_url provided"}

    # Download the paper using wget
    paper_file_path = await get_paper(req.paper_url)
    print(f'Paper file path: {paper_file_path}')
    paper_content = pdfplumber.open(paper_file_path).pages
    print(f'Paper content: {paper_content}')

    paper_tldr = await generate_tldr(paper_content)
    print(f'Paper tldr: {paper_tldr}')
    return paper_tldr

