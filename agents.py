from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
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
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=st.secrets["GEMINI_API_KEY"],
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
    ("system", (
        "You are an expert research writer. You produce structured, scannable, "
        "information-dense reports. You never invent URLs — you only use sources provided "
        "to you. You write tight prose: short paragraphs, no filler, no repetition."
    )),
    ("human", """Write a research report on: {topic}

Use ONLY the research material below. Do not fabricate facts or sources.

RESEARCH MATERIAL:
{research}

VERIFIED SOURCE URLS (use these exactly in the Sources section, do not invent others):
{sources}

Follow this structure EXACTLY. Use markdown headings.

# <Report Title — specific to the topic, not generic>

## Introduction
- 120–150 words maximum.
- State what the topic is, why it matters now, and what the report covers.
- No filler sentences, no "in this report we will discuss" preambles.

## <Section 1 Heading>
## <Section 2 Heading>
## <Section 3 Heading>
## <Section 4 Heading>
## <Section 5 Heading>
[Optional: ## <Section 6 Heading>, ## <Section 7 Heading>]

Rules for sections:
- Produce between 5 and 7 sections total (not fewer, not more).
- Each section heading must be specific (e.g., "Current Industry Adoption", not "Overview" or "Background").
- Each section is EITHER 2–3 short paragraphs (max 4 sentences each) OR a tight bulleted list of 4–6 points. Pick whichever fits the content. Do not mix both inside one section.
- Sections must cover distinct angles: e.g., context, technical mechanism, key players, recent developments, challenges/risks, outlook. Do not repeat ideas across sections.

## Conclusion
- 100 words maximum.
- Synthesize the key takeaway. No new facts. No bullet points.

## Sources
- List 3–5 URLs from the VERIFIED SOURCE URLS block above, one per line, as a markdown bulleted list.
- Do not include any URL not in that block.
- Do not add descriptions — URL only.

Output the report in clean markdown. No preamble, no closing remarks outside the structure above.
{revision_instructions}"""),
])


def get_writer_chain():
    llm = get_llm()

    def build_messages(inputs: dict):
        revision_instructions = ""
        if inputs.get("weaknesses"):
            revision_instructions = (
                "\n\n## REVISION INSTRUCTIONS\n"
                "This is a revision pass. Address ALL of the following weaknesses from the "
                "previous draft while keeping the 5–7 section structure above:\n"
                + inputs["weaknesses"]
            )
        return writer_prompt.format_messages(**{**inputs, "revision_instructions": revision_instructions})

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