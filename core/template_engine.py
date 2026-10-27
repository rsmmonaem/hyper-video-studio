#!/usr/bin/env python3
"""
Hyper Video Studio - Zero-Dependency HTML Template Compiler
Parses and compiles templates with support for:
- {{ var }} and {{ object.prop }}
- {{ "%.1f"|format(var) }}
- {{ var|safe }} and {{ var|upper }}
- {% for item in list %} ... {% endfor %}
"""

import re
import json

def resolve_var(context, expr):
    expr = expr.strip()
    # Format pattern: "%.1f"|format(var)
    format_match = re.match(r'["\'](.*?)["\']\|format\((.*?)\)', expr)
    if format_match:
        fmt_str, var_name = format_match.groups()
        val = resolve_var(context, var_name)
        try:
            return fmt_str % float(val)
        except Exception:
            return str(val)

    # Safe filter
    if expr.endswith("|safe"):
        return resolve_var(context, expr[:-5])
    
    # Upper filter
    if expr.endswith("|upper"):
        val = resolve_var(context, expr[:-6])
        return str(val).upper()

    parts = expr.split(".")
    curr = context
    for p in parts:
        p = p.strip()
        if isinstance(curr, dict) and p in curr:
            curr = curr[p]
        elif hasattr(curr, p):
            curr = getattr(curr, p)
        else:
            return ""
    if isinstance(curr, (dict, list)):
        return json.dumps(curr, ensure_ascii=False)
    return str(curr)

def render_template(template_content, context):
    # 1. Process {% for item in list %} ... {% endfor %}
    for_pattern = re.compile(r'\{%\s*for\s+(\w+)\s+in\s+([\w\.]+)\s*%\}(.*?)\{%\s*endfor\s*%\}', re.DOTALL)
    
    def replace_for(match):
        item_name, list_expr, block = match.groups()
        items = context
        for p in list_expr.split("."):
            if isinstance(items, dict) and p in items:
                items = items[p]
            else:
                items = []
                break
        if not isinstance(items, list):
            items = []
        
        rendered_blocks = []
        for it in items:
            sub_ctx = dict(context)
            sub_ctx[item_name] = it
            rendered_blocks.append(render_template(block, sub_ctx))
        return "".join(rendered_blocks)

    rendered = for_pattern.sub(replace_for, template_content)

    # 2. Process {{ expression }}
    var_pattern = re.compile(r'\{\{\s*(.*?)\s*\}\}')
    def replace_var(match):
        expr = match.group(1)
        return str(resolve_var(context, expr))

    return var_pattern.sub(replace_var, rendered)
