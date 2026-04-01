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

# Example 2: OCR
# Tool: read_text(
#   working_dir="/absolute/path/to/project",
#   image_path="assets/screenshot.png"
# )

# Example 3: generic analysis
# Tool: analyze_image(
#   working_dir="/absolute/path/to/project",
#   image_path="assets/diagram.png",
#   prompt="Analyze this architecture diagram and explain the data flow",
#   model="qwen-2.5-vl"
# )

# Example 4: semantic description
# Tool: describe_image(
#   working_dir="/absolute/path/to/project",
#   image_path="assets/photo.jpg"
# )

# Example 5: object extraction
# Tool: identify_objects(
#   working_dir="/absolute/path/to/project",
#   image_path="assets/workspace.png"
# )

# Example 6: integration profile for nanobot
# Tool: get_nanobot_profile()

# Example 7: security telemetry
# Tool: get_security_metrics()

# Example 8: rollout policy status
# Tool: get_rollout_status()

# Example 9: tool access policy status
# Tool: get_access_policy_status()
