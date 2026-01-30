"""LLM-based data extractor using Claude."""

import json
from typing import Dict, Any
from anthropic import Anthropic
from .config import settings
from .models import PromptTemplate, ExtractionSchema, WebsiteData


class LLMExtractor:
    """Extract structured data using Claude."""
    
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set")
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    def extract(
        self,
        content: WebsiteData,
        prompt_template: PromptTemplate,
        schema: ExtractionSchema,
        **template_vars
    ) -> Dict[str, Any]:
        """Extract structured data from content."""
        
        rendered_prompt = prompt_template.render(
            content=content.markdown,
            url=content.url,
            title=content.title or "",
            **template_vars
        )
        
        schema_description = self._build_schema_description(schema)
        
        full_prompt = f"""{rendered_prompt}

{schema_description}

IMPORTANT: Return ONLY valid JSON matching the schema. No markdown, no explanation, just the JSON object."""
        
        response = self.client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": full_prompt}]
        )
        
        response_text = response.content[0].text
        extracted_data = self._parse_json_response(response_text)
        validated_data = self._validate_against_schema(extracted_data, schema)
        
        return validated_data
    
    def _build_schema_description(self, schema: ExtractionSchema) -> str:
        """Build a description of the schema for Claude."""
        lines = [
            f"Extract the following fields according to this schema:",
            f"",
            f"Schema: {schema.name}",
            f"Description: {schema.description}",
            f"",
            f"Fields to extract:",
        ]
        
        for field_name, field_info in schema.fields.items():
            field_type = field_info.get("type", "string")
            field_desc = field_info.get("description", "")
            required = field_info.get("required", False)
            
            req_marker = " (REQUIRED)" if required else " (optional)"
            lines.append(f"- {field_name} ({field_type}){req_marker}: {field_desc}")
        
        lines.append("")
        lines.append("Return as JSON with these exact field names.")
        
        return "\n".join(lines)
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from Claude's response."""
        text = response_text.strip()
        
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Could not parse JSON from response: {e}")
    
    def _validate_against_schema(
        self, 
        data: Dict[str, Any], 
        schema: ExtractionSchema
    ) -> Dict[str, Any]:
        """Validate extracted data against schema."""
        validated = {}
        
        for field_name, field_info in schema.fields.items():
            required = field_info.get("required", False)
            default = field_info.get("default")
            
            if field_name in data:
                validated[field_name] = data[field_name]
            elif required:
                raise ValueError(f"Required field '{field_name}' not found")
            elif default is not None:
                validated[field_name] = default
        
        return validated
