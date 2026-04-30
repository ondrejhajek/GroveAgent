import logfire
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from system.agent import create_agent
from system.constants import CONFIG_FILE
logfire.configure()
logfire.instrument_pydantic_ai()
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import HasMatchingSpan
import os
from dotenv import load_dotenv
load_dotenv()

# Create a dataset with test cases
# dataset = Dataset(
#     name='uppercase_tests',
#     cases=[
#         Case(
#             inputs='hlavní město Francie, česky, velkými písmeny',
#             expected_output='HELLO WORLD',
#             metadata={'author': 'John Doe'},
#         ),
#     ],
#     evaluators=[
#         Contains(value='PAŘÍŽ', case_sensitive=True),  # Check contains "HELLO"
#     ],
# )

dataset = Dataset(
    name='tool_verification',
    cases=[Case(inputs='zjisti výstup bash příkazu "uname"')],
    evaluators=[
        HasMatchingSpan(#https://pydantic.dev/docs/ai/evals/evaluators/span-based/
            query={'name_contains': 'running_tool'},
            evaluation_name='used_run_bash',
        )
    ],
)

models = ["minimax/minimax-m2.5", "google/gemma-4-31b-it", "openai/gpt-5.4-nano"]

for model in models:

    def run_agent(inpt: str) -> str:
        mdl = OpenRouterModel(
            model,
            provider=OpenRouterProvider(
                api_key=os.environ['OPENROUTER_API_KEY']
            )
        )
        agent = create_agent(CONFIG_FILE)
        agent.model = mdl
        result = agent.run_sync(inpt)
        return result.output

    # Run the evaluation
    report = dataset.evaluate_sync(run_agent, repeat=1)
    # Print the results
    report.print(include_input=True, include_output=True)