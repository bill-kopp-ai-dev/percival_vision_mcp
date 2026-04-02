"""
Examples for Percival Vision MCP tools.

All tool outputs return structured JSON envelopes:
- ok/data/meta/request_id (success)
- ok/error/code/meta/request_id (error)

Compatibility:
- `working_dir` is recommended.
- If omitted, server derives a safe value (absolute image parent or current cwd).
"""

# Example 1: discover models
# Tool: list_available_vision_models(force_refresh=False)

# Example 2: intent-based recommendation from local catalog
# Tool: recommend_vision_model_for_intent(
#   task_type="document_qa",
#   intent="ocr de recibos com prioridade de custo",
#   max_results=3,
#   prioritize_cost=True
# )

# Example 3: list local catalog cards
# Tool: list_vision_model_cards(
#   task_type="general_vision",
#   limit=10,
#   offset=0,
#   fields="id,name,task_types,cost_estimation,capabilities"
# )

# Example 4: verify selected model before execution
# Tool: verify_vision_model_availability(
#   model_id="openai-gpt-4o-mini-2024-07-18",
#   task_type="ocr"
# )

# Example 5: OCR
# Tool: read_text(
#   working_dir="/absolute/path/to/project",
#   image_path="assets/screenshot.png"
# )

# Example 6: generic analysis
# Tool: analyze_image(
#   working_dir="/absolute/path/to/project",
#   image_path="assets/diagram.png",
#   prompt="Analyze this architecture diagram and explain the data flow",
#   model="qwen-2.5-vl"
# )

# Example 7: semantic description
# Tool: describe_image(
#   working_dir="/absolute/path/to/project",
#   image_path="assets/photo.jpg"
# )

# Example 8: object extraction
# Tool: identify_objects(
#   working_dir="/absolute/path/to/project",
#   image_path="assets/workspace.png"
# )

# Example 9: integration profile for nanobot
# Tool: get_nanobot_profile()

# Example 10: security telemetry
# Tool: get_security_metrics()

# Example 11: rollout policy status
# Tool: get_rollout_status()

# Example 12: tool access policy status
# Tool: get_access_policy_status()
