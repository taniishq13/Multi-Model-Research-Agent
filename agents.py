from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from tools import web_search , scrape_url
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


class CritiqueResult(BaseModel):
    score: int = Field(..., ge=1, le=10, description="Quality score from 1 to 10")
    strengths: list[str] = Field(..., description="List of report strengths")
    weaknesses: list[str] = Field(..., description="List of areas to improve")
    verdict: str = Field(..., description="One-line overall verdict")


def get_llm():
    return ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=st.secrets["GROQ_API_KEY"],
        temperature=0.3
    )


#1st agent 
def build_search_agent():
    return create_agent(
        model = get_llm(),
        tools= [web_search]
    )

#2nd agent 

def build_reader_agent():
    return create_agent(
        model = get_llm(),
        tools = [scrape_url]
    )


#writer chain

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

revision_writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Revise the following report addressing these weaknesses.

Topic: {topic}

Research Gathered:
{research}

Previous Report:
{previous_report}

Weaknesses to address:
{weaknesses}

Structure the revised report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

def get_writer_chain():
    llm = get_llm()

    def build_messages(inputs: dict):
        if inputs.get("previous_report"):
            return revision_writer_prompt.format_messages(**inputs)
        return writer_prompt.format_messages(**inputs)

    return RunnableLambda(build_messages) | llm | StrOutputParser()

#critic_chain 

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Provide a score (1-10), a list of strengths, a list of weaknesses/areas to improve, and a one-line verdict."""),
])

def get_critic_chain():
    llm = get_llm()
    return critic_prompt | llm.with_structured_output(CritiqueResult)