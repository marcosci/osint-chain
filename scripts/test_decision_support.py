#!/usr/bin/env python3
"""
Test the decision support tool with the Mali question.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.tools.decision_support import decision_support_tool

# Test the tool
print("🚀 Testing Decision Support Tool\n")

result = decision_support_tool.invoke({
    "question": "How to stabilize Mali politically",
    "context": "Focus on practical, implementable solutions given current constraints"
})

print(result)

# Save to file
output_file = Path("mali_analysis.md")
output_file.write_text(result)
print(f"\n💾 Full analysis saved to: {output_file}")
