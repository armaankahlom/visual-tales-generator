from openai import OpenAI
import json
import replicate
import os
from dotenv import load_dotenv

load_dotenv()

# Separate variables for each key
openai_api_key = os.getenv("OPENAI_API_KEY")
replicate_api_key = os.getenv("REPLICATE_API_TOKEN")

if not openai_api_key:
    raise ValueError("OpenAI API key not found. Make sure you have set OPENAI_API_KEY in your environment.")
if not replicate_api_key:
    raise ValueError("Replicate API token not found. Make sure you have set REPLICATE_API_TOKEN in your environment.")

# Initialize OpenAI client with openai_api_key
client = OpenAI(api_key=openai_api_key)

def get_user_parameters():
    """Collect only character-related parameters from user"""
    print("Please enter the following story parameters:")
    return {
        "V0": input("Enter (Main Character): "),
        "V3": input("Enter (Hero 1 - Primary): "),
        "V4": input("Enter (Hero 2 - Secondary): "),
        "V5": input("Enter (Hero 3 - Support): ")
    }


def extract_story_elements(sentence):
    """Extract V1 (location) and V2 (conflict) from a given sentence"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """Analyze the story sentence to extract:
1. V1 (Primary location/setting) - Where the scene occurs
2. V2 (Core conflict) - The central problem/struggle
Return JSON format: {"V1": "...", "V2": "..."}"""
            },
            {"role": "user", "content": f"Sentence: {sentence}"}
        ],
        response_format={"type": "json_object"}
    )
    result = json.loads(response.choices[0].message.content)
    return result["V1"], result["V2"]


def generate_image_prompts(sentence, params):
    """
    Generate 3 Flux-optimized image prompts for a sentence using provided parameters.
    Ensures:
    1. Image 1: Secondary hero ONLY (wide shot)
    2. Image 2: Main character ONLY (medium shot)
    3. Image 3: Conflict object/environment ONLY (close-up)
    No character overlap between images
    - Complies with Pixar-style 3D cartoon animation rules.
    """
    prompt_template = (
    f"""Generate 3 Flux-optimized image prompts for: "{sentence}"
    **Parameters:**
    - Location: {{V1}}
    - Conflict: {{V2}}
    - Main Character: {{V0}} (appears ONLY in Image 2)
    - Heroes: {{V3}}, {{V4}}, {{V5}} (each appears in exactly ONE image)
    - Style: Pixar 3D cartoon (smooth textures, vibrant colors, exaggerated proportions)

    **Strict Rules:**
    1. **Image 1 (Secondary Action):**
    - Focus on ONE secondary hero ({{V3}}, {{V4}}, or {{V5}})
    - Show their action related to the conflict
    - Wide shot with environment context
    - No main character ({{V0}})

    2. **Image 2 (Main Participation):**
    - Feature ONLY {{V0}} addressing the conflict
    - Medium shot showing facial expression/action
    - No other heroes present

    3. **Image 3 (Environmental Focus):**
    - Show physical evidence/object related to conflict
    - Close-up of item/environmental detail
    - Zero characters visible

    **Format Requirements:**
    - 80-100 words per prompt
    - End ALL prompts with "in Pixar 3D cartoon animation"
    - Concrete details only (no narrative phrases)
    - Maintain consistent lighting/textures across all images
    - One character max per frame (except background extras)
    """
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a storyboard artist. You will create a visually consistent, sequential, "
                    "Pixar-style narrative in exactly 3 prompts, each building on the previous. "
                    "Ensure that once a description for a character is defined, the same description is used consistently in all prompts."
                )
            },
            {
                "role": "user",
                "content": prompt_template.format(**params)
            }
        ]
    )

    return response.choices[0].message.content.strip()

# Prompt user for parameters
story_params = get_user_parameters()

# Load JSON input (make sure input_sentence.json exists in the same directory)
current_dir = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(current_dir, "input_sentence.json")

with open(json_file_path, "r", encoding="utf-8") as f:
    story_sentences = json.load(f)

# Create an output directory for images if it doesn't exist
os.makedirs("story", exist_ok=True)

# Generate and save images
for sent_key, sentence in story_sentences.items():
    print(f"\nProcessing {sent_key}: {sentence}")

    V1, V2 = extract_story_elements(sentence)

    current_params = {
        "V0": story_params["V0"],
        "V1": V1,
        "V2": V2,
        "V3": story_params["V3"],
        "V4": story_params["V4"],
        "V5": story_params["V5"]
    }

    # Generate prompts
    prompts = generate_image_prompts(sentence, current_params)
    print("Generated Prompts:\n", prompts)

    # Split into lines and remove empty ones
    lines = [line.strip() for line in prompts.split('\n') if line.strip()]

    merged_prompts = []
    current_block = ""

    for line in lines:
        if line.startswith("**Image"):
            # If there's already text in current_block, finalize it
            if current_block:
                merged_prompts.append(current_block.strip())
            # Start a new block with this heading
            current_block = line
        else:
            current_block += " " + line

    # Append the last block if it exists
    if current_block:
        merged_prompts.append(current_block.strip())

    # Now you have exactly three consolidated prompts
    prompt_lines = merged_prompts[:3]

    for idx, prompt_line in enumerate(prompt_lines, start=1):
        flux_input = {
            "prompt": prompt_line,
            # Guidance level for image generation, adjust for more or less fidelity to the prompt
            "num_outputs": 1,
            # "prompt_strength": 0.8,  # Adjust prompt strength for img2img (set to 1.0 for full adherence)
            # "num_inference_steps": 28,  # Number of denoising steps (higher steps = better quality)
            "output_format": "jpg"
        }
        outputs = replicate.run("black-forest-labs/flux-dev", input=flux_input)

        # Save each image
        for out_index, item in enumerate(outputs):
            image_path = f"story/{sent_key}_prompt{idx}.jpg"
            with open(image_path, "wb") as img_file:
                img_file.write(item.read())
            print(f"Saved image: {image_path}")