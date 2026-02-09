from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from ..schemas.state import SummaryOutput

# client = AsyncOpenAI(
#     base_url='http://localhost:11434/v1',
#     api_key='ollama',
# )

# for Gemini, you might use:

# from pydantic_ai import Agent
# from pydantic_ai.models.google import GoogleModel
# from pydantic_ai.providers.google import GoogleProvider

# provider = GoogleProvider(api_key='your-api-key')
# model = GoogleModel('gemini-3-pro-preview', provider=provider)
# agent = Agent(model)

model = OpenAIChatModel(
            model_name='llama3.1', 
            provider=OpenAIProvider(
                base_url='http://localhost:11434/v1', 
                api_key='ollama'
            )
        )

translator_agent = Agent(
    model,
    instructions="Translate the following text to Hindi.",
    model_settings={"temperature": 0},
    retries=3,
)

#  result_type=CountOutput, system_prompt="Count words in the text."
